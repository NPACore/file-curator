#!/usr/bin/env python3
"""
Shim Notify Gear
================

This script performs a Z-shim quality check on Siemens MRI DICOM data,
intended for use as a Flywheel gear or standalone utility.

It extracts the Z-shim offset from a Siemens CSA DICOM header, maps the
scanner’s station ID to a project-specific label (e.g., PRISMA1), and sends
a notification email indicating whether the shim value meets the expected
threshold.

Typical Use Cases
-----------------
- As a Flywheel gear: automatically check shim quality upon DICOM upload
- As a standalone CLI script for local QA pipelines

Inputs
------
- ZIP archive containing Siemens DICOM files
- A TOML config file with scanner station map and Z-thresholds
- A TOML config file listing email recipients and SMTP info

Workflow Summary
----------------
1. Extract the first DICOM file from the ZIP archive.
2. Parse Siemens CSA headers to extract the Z-shim offset.
3. Determine scanner type from `StationName` using a station map.
4. Compare Z value to scanner-specific threshold.
5. Notify recipients with pass/fail result via SMTP.
6. Optionally update Flywheel session metadata (if running inside a gear).

Example CLI Usage
-----------------
python shim_notify.py dicom.zip shim-emails.toml shim_config.toml

See Also
--------
- `FileCurator` class in flywheel_gear_toolkit.utils.curator
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
    logging.warning("Old Python %s – using 'toml' fallback", sys.version)

from smtplib import SMTP
from email.message import EmailMessage
from flywheel_gear_toolkit.utils.curator import FileCurator

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from nibabel.nicom import csareader

log = logging.getLogger("shimtest")


def load_toml_config(path: str) -> dict:
    """
    Load station map and z thresholds from a TOML file.

    Parameters
    ----------
    path : str
        Path to the TOML config file.

    Returns
    -------
    dict
        Dictionary with 'station_map' and 'z_thresholds'.
    """
    with open(path, "rb") as f:
        return toml.load(f)


def station_to_name(station_id: str, station_map: dict) -> str:
    return station_map.get(station_id, station_id)


def notify_message(scanner: str, z: float, z_thresholds: dict) -> str:
    threshold = z_thresholds.get(scanner, 10000)
    if z >= threshold:
        return f"{scanner} ✅: z={z:.2f} ≥ {threshold:.2f} – value okay."
    else:
        return f"{scanner} ⛔: z={z:.2f} < {threshold:.2f} – BAD SHIM"


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
    with ZipFile(zfname) as zf:
        for entry in zf.filelist:
            if entry.file_size > 0:
                with zf.open(entry.filename) as fh:
                    return pydicom.dcmread(fh)
    raise ValueError("No valid DICOM found in zip.")


def read_emails(config: dict) -> list[dict]:
    recips = config["recipients"]
    return [
        {
            "host": recips["host"],
            "from": recips["from"],
            "to": to
        }
        for to in recips["to"]
    ]


def main(zip_path: str, config_path: str):
    """
    Run shim QC check and send email notifications.

    Parameters
    ----------
    zip_path : str
        Path to ZIP file containing DICOMs.
    email_configs : list of dict
        Email configuration dictionary list.
    config_path : str
        Path to shim_config.toml with station map and thresholds.
    """
    config = load_toml_config(config_path)
    station_map = config["station_map"]
    z_thresholds = config["z_thresholds"]
    email_configs = read_emails(config)

    dcm = first_dicom_from_zip(zip_path)
    z = read_z(dcm)
    scanner = station_to_name(dcm.StationName, station_map)
    print(f"# Z={z:.2f} from {scanner} (StationName={dcm.StationName})")

    msg = notify_message(scanner, z, z_thresholds)
    print(msg)

    emoji = "✅" if z >= z_thresholds.get(scanner, 10000) else "⛔"
    subject = f"{scanner} {emoji} Shim QC Alert"

    for entry in email_configs:
        try:
            send_email(
                subject=subject,
                body=msg,
                sender=entry["from"],
                recipient=entry["to"],
                host=entry["host"]
            )
        except Exception as e:
            log.warning(f"Failed to send to {entry['to']} via {entry['host']}: {e}")


class Curator(FileCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None

    def curate_file(self, file_: Dict[str, Any]):
        zip_path = file_["location"]["path"]
        config_path = self.context.get_input_path("additional-input-one")
        main(zip_path, config_path)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <dicom.zip> <shim_settings.toml>")
        sys.exit(1)
    zip_path = sys.argv[1]
    config_path = sys.argv[2]
    main(zip_path, config_path)

