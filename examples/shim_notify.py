#!/usr/bin/env python3
"""
Shim QC Script

This script checks the Z-shim offset from a Siemens CSA DICOM header,
maps the scanner serial number to a PRISMA label, and sends a notification
email indicating whether the shim value meets the threshold.

It loads station map and threshold values from a TOML file.
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


def read_emails(toml_path: str) -> list[dict]:
    with open(toml_path, "rb") as fh:
        config = toml.load(fh)
    return config["recipients"]


def main(zip_path: str, email_configs: list[dict], config_path: str):
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
        toml_path = self.context.get_input_path("additional-input-one")
        config_path = self.context.get_input_path("additional-input-two")
        email_configs = read_emails(toml_path)
        main(zip_path, email_configs, config_path)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <dicom.zip> <emails.toml> <shim_config.toml>")
        sys.exit(1)
    zip_path = sys.argv[1]
    email_configs = read_emails(sys.argv[2])
    config_path = sys.argv[3]
    main(zip_path, email_configs, config_path)

