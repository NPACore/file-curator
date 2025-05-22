#!/usr/bin/env python3
"""
Shim QC: Check Z-shim offset from DICOM CSA header,
map scanner serial to PRISMA label, and notify via email.

NB. for smtp host, pitt allows plaintext un-authed connections from whitelisted IPs. for server host name, see 'nslookup -type=mx pitt.edu'

"""

import logging
import os
import re
import sys
import warnings
from zipfile import ZipFile
from typing import Any, Dict

import pydicom
from pydicom.misc import is_dicom

try:
    import tomllib as toml  # Python 3.11+
except:
    import toml
    logging.warning("old python %s. using 'toml' library to read email settings", sys.version)

from smtplib import SMTP
from email.message import EmailMessage
from flywheel_gear_toolkit.utils.curator import FileCurator

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from nibabel.nicom import csareader

log = logging.getLogger("shimtest")

# Map StationName → PRISMA label
STATION_MAP = {
    "MRC67078": "PRISMA1",
    "AWP167046": "PRISMA2",
    "MRC35073": "PRISMA3",
}

# Scanner-specific Z-thresholds
Z_THRESHOLDS = {
    "PRISMA1": 9931.513661,
    "PRISMA2": 4505.258657,
    "PRISMA3": 11652.571269,
}


def station_to_name(station_id: str) -> str:
    return STATION_MAP.get(station_id, station_id)

def send_email(subject: str, body: str, sender: str, recipient: str, host: str = "localhost"):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)

    log.info(f"Connecting to SMTP server: {host}")
    with SMTP(host, timeout=30) as srv:
        srv.set_debuglevel(1)
        srv.send_message(msg)


def read_z(dcm: pydicom.Dataset) -> float:
    """
    Parse sGRADSPEC.asGPAData[0].lOffsetZ from Siemens CSA header
    """
    csa = dcm.get((0x0029, 0x1020))
    csa_s = csareader.read(csa.value)
    asccov = csa_s["tags"]["MrPhoenixProtocol"]["items"][0]
    match = re.search(r"sGRADSPEC.asGPAData\[0\].lOffsetZ\s*=\s*([^\s]+)", asccov)
    return float(match.group(1))


def update_db(fw, dest_id, z: float):
    container = fw.get(dest_id)
    if not container:
        raise Exception(f"No container with id '{dest_id}'")
    sess = fw.get(container.parents.session)
    sess.update_info({"z": z})
    log.info(f"Updated Flywheel session info: z = {z}")


def first_dicom_from_zip(zfname: str) -> pydicom.Dataset:
    """
    Extract first DICOM file from a zip
    """
    with ZipFile(zfname) as zf:
        for entry in zf.filelist:
            if entry.file_size > 0:
                with zf.open(entry.filename) as fh:
                    return pydicom.dcmread(fh)
    raise ValueError("No valid DICOM found in zip.")


def read_emails(toml_path: str) -> tuple[str, str, str]:
    with open(toml_path, "rb") as fh:
        config = toml.load(fh)
    return (
        config["from"],
        config.get("to", config["from"]),
        config.get("host", "localhost")
    )


def main(zip_path: str, from_addr: str, to_addr: str, host: str = "localhost"):
    dcm = first_dicom_from_zip(zip_path)
    z = read_z(dcm)
    scanner = station_to_name(dcm.StationName)

    threshold = Z_THRESHOLDS.get(scanner, 10000)
    failed = z <= threshold
    log.info(f"Z={z:.2f} from {scanner} (StationName={dcm.StationName}) <= threshold {threshold}? {failed}")

    if failed:
        subj = f"[{scanner}] FAILED (z={z} <= {threshold})" 
        msg = f"!!!ERROR!!! BAD SHIM\n{scanner}: z={z:.2f} (threshold={threshold:.2f})."
    else:
        subj = f"[{scanner}] shim okay (z={z} <= {threshold})" 
        msg = f"shim looks okay for {scanner}; z={z:.2f} (threshold={threshold:.2f})."
    print(msg)

    send_email(subject=subj, body=msg, sender=from_addr, recipient=to_addr, host=host)


class Curator(FileCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None

    def curate_file(self, file_: Dict[str, Any]):
        zip_path = file_["location"]["path"]
        toml_path = self.context.get_input_path("additional-input-one")
        from_addr, to_addr, host = read_emails(toml_path)
        main(zip_path, from_addr, to_addr, host)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <dicom.zip> <emails.toml>")
        sys.exit(1)
    zip_path = sys.argv[1]
    from_addr, to_addr, host = read_emails(sys.argv[2])
    main(zip_path, from_addr, to_addr, host)

