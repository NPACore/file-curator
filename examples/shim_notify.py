#!/usr/bin/env python3
"""
Shim QC Script

This script checks the Z-shim offset from a Siemens CSA DICOM header,
maps the scanner serial number to a PRISMA label, and sends a notification
email indicating whether the shim value meets the threshold.

For SMTP, UPMC and Pitt typically use Exchange Online Protection.
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
    """
    Map a scanner StationName ID to a human-readable PRISMA label.

    Parameters
    ----------
    station_id : str
        The scanner's StationName from DICOM headers.

    Returns
    -------
    str
        Human-readable PRISMA label or original station ID if unknown.
    """
    return STATION_MAP.get(station_id, station_id)


def notify_message(scanner: str, z: float) -> str:
    """
    Generate a notification message based on the Z-shim value.

    Parameters
    ----------
    scanner : str
        Scanner label (e.g. "PRISMA1").
    z : float
        Z-shim offset value.

    Returns
    -------
    str
        Message indicating if shim is OK or bad.
    """
    threshold = Z_THRESHOLDS.get(scanner, 10000)
    if z >= threshold:
        return f"{scanner} ✅: z={z:.2f} ≥ {threshold:.2f} – value okay."
    else:
        return f"{scanner} ⛔: z={z:.2f} < {threshold:.2f} – BAD SHIM"


def send_email(subject: str, body: str, sender: str, recipient: str, host: str = "localhost"):
    """
    Send an email notification.

    Parameters
    ----------
    subject : str
        Email subject.
    body : str
        Email body.
    sender : str
        From address.
    recipient : str
        To address.
    host : str, optional
        SMTP host server (default is localhost).
    """
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
    Read the Z-shim offset from the Siemens CSA header.

    Parameters
    ----------
    dcm : pydicom.Dataset
        Parsed DICOM dataset.

    Returns
    -------
    float
        Extracted Z-shim offset value.
    """
    csa = dcm.get((0x0029, 0x1020))
    csa_s = csareader.read(csa.value)
    asccov = csa_s["tags"]["MrPhoenixProtocol"]["items"][0]
    match = re.search(r"sGRADSPEC.asGPAData\[0\].lOffsetZ\s*=\s*([^\s]+)", asccov)
    return float(match.group(1))


def update_db(fw, dest_id, z: float):
    """
    Update Flywheel session info with Z-shim value.

    Parameters
    ----------
    fw : flywheel.Client
        Flywheel client instance.
    dest_id : str
        Destination container ID (usually an analysis or acquisition).
    z : float
        Z-shim offset value to store.
    """
    container = fw.get(dest_id)
    if not container:
        raise Exception(f"No container with id '{dest_id}'")
    sess = fw.get(container.parents.session)
    sess.update_info({"z": z})
    log.info(f"Updated Flywheel session info: z = {z}")


def first_dicom_from_zip(zfname: str) -> pydicom.Dataset:
    """
    Extract and return the first valid DICOM file from a ZIP archive.

    Parameters
    ----------
    zfname : str
        Path to ZIP file.

    Returns
    -------
    pydicom.Dataset
        First readable DICOM dataset found in the ZIP.
    """
    with ZipFile(zfname) as zf:
        for entry in zf.filelist:
            if entry.file_size > 0:
                with zf.open(entry.filename) as fh:
                    return pydicom.dcmread(fh)
    raise ValueError("No valid DICOM found in zip.")


def read_emails(toml_path: str) -> list[dict]:
    """
    Load email recipient configuration from TOML file.

    Parameters
    ----------
    toml_path : str
        Path to the TOML config file.

    Returns
    -------
    list of dict
        Parsed recipient configuration.
    """
    with open(toml_path, "rb") as fh:
        config = toml.load(fh)
    return config["recipients"]


def main(zip_path: str, email_configs: list[dict]):
    """
    Run shim QC check and send email notifications.

    Parameters
    ----------
    zip_path : str
        Path to ZIP file containing DICOMs.
    email_configs : list of dict
        Email configuration dictionary list.
    """
    dcm = first_dicom_from_zip(zip_path)
    z = read_z(dcm)
    scanner = station_to_name(dcm.StationName)
    print(f"# Z={z:.2f} from {scanner} (StationName={dcm.StationName})")

    msg = notify_message(scanner, z)
    print(msg)

    emoji = "✅" if z >= Z_THRESHOLDS.get(scanner, 10000) else "⛔"
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
    """
    Flywheel Curator class to run shim QC within Flywheel gear.

    Attributes
    ----------
    reporter : Any
        Optional placeholder for future reporting extension.
    """

    def __init__(self, **kwargs):
        """
        Initialize the Curator with FileCurator context.
        """
        super().__init__(**kwargs)
        self.reporter = None

    def curate_file(self, file_: Dict[str, Any]):
        """
        Process a file by performing shim QC and sending notifications.

        Parameters
        ----------
        file_ : dict
            Metadata for the input file.
        """
        zip_path = file_["location"]["path"]
        toml_path = self.context.get_input_path("additional-input-one")
        email_configs = read_emails(toml_path)
        main(zip_path, email_configs)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <dicom.zip> <emails.toml>")
        sys.exit(1)
    zip_path = sys.argv[1]
    email_configs = read_emails(sys.argv[2])
    main(zip_path, email_configs)

