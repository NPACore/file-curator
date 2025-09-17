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
from typing import Any, Dict, Tuple

import pydicom
from pydicom.misc import is_dicom

try:
    import tomllib as toml  # Python 3.11+
except Exception:
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
    with open(path, "rb") as f:
        return toml.load(f)


def _normalize_recipients(to_value) -> list[str]:
    """Accept list or comma-separated string and return a list of recipients."""
    if isinstance(to_value, list):
        return [x.strip() for x in to_value if x and isinstance(x, str)]
    if isinstance(to_value, str):
        return [x.strip() for x in to_value.split(",") if x.strip()]
    return []


def parse_config(config: dict) -> Tuple[dict, dict, list[dict]]:
    """
    Returns:
      scanner_name_by_id: dict[str, str]  # e.g., {'AWP167046': 'P2'}
      threshold_by_id:    dict[str, float]
      email_entries:      list[{'host','from','to'}]  # expanded per-address
    Supports both:
      New style:
        [[scanner]] id, shortname, threshold
        [[emails]] host, from, to
      Old style:
        [station_map] id -> longname
        [z_thresholds] longname -> threshold
        [recipients] host, from, to(list)
    """
    scanner_name_by_id: dict[str, str] = {}
    threshold_by_id: dict[str, float] = {}
    email_entries: list[dict] = []

    # ---- New-style emails: [[emails]]
    if "emails" in config and isinstance(config["emails"], list):
        for e in config["emails"]:
            host = e.get("host")
            sender = e.get("from")
            tos = _normalize_recipients(e.get("to", []))
            if not host or not sender or not tos:
                continue
            for addr in tos:
                email_entries.append({"host": host, "from": sender, "to": addr})

    # ---- Old-style recipients (back-compat)
    if not email_entries and "recipients" in config:
        recips = config["recipients"]
        host = recips.get("host")
        sender = recips.get("from")
        tos = _normalize_recipients(recips.get("to", []))
        if host and sender and tos:
            for addr in tos:
                email_entries.append({"host": host, "from": sender, "to": addr})

    # ---- New-style scanners: [[scanner]]
    if "scanner" in config and isinstance(config["scanner"], list):
        for s in config["scanner"]:
            sid = str(s.get("id", "")).strip()
            if not sid:
                continue
            shortname = str(s.get("shortname", sid)).strip()
            scanner_name_by_id[sid] = shortname
            try:
                threshold_by_id[sid] = float(s.get("threshold"))
            except (TypeError, ValueError):
                # Sensible default if missing/invalid
                threshold_by_id[sid] = 10000.0

    # ---- Old-style scanners (back-compat): station_map + z_thresholds
    if not scanner_name_by_id and "station_map" in config:
        station_map = config.get("station_map", {})
        z_thresholds = config.get("z_thresholds", {})
        for sid, longname in station_map.items():
            # Keep display name as whatever you used before; caller can treat it like shortname
            display = str(longname).strip() if longname else str(sid)
            scanner_name_by_id[sid] = display
            # Thresholds were keyed by longname in old config
            try:
                threshold_by_id[sid] = float(z_thresholds.get(display, 10000.0))
            except (TypeError, ValueError):
                threshold_by_id[sid] = 10000.0

    return scanner_name_by_id, threshold_by_id, email_entries


def notify_message(display_name: str, z: float, threshold: float) -> str:
    if z >= threshold:
        return f"{display_name} ✅: z={z:.2f} ≥ {threshold:.2f} – value okay."
    else:
        return f"{display_name} ⛔: z={z:.2f} < {threshold:.2f} – BAD SHIM"


def send_email(
    subject: str, body: str, sender: str, recipient: str, host: str = "localhost"
):
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
    """
    UNUSED
    Add z value to flywheel database at session level for searching.
    This is done by heavier t/SNR QC pipeline.
    @param fw  flywheel client object
    @param dest_id id of acquisition file (use parents.session)
    @param z    z-shim value to insert into DB
    """
    container = fw.get(dest_id)
    if not container:
        raise Exception(f"No container with id '{dest_id}'")
    sess = fw.get(container.parents.session)
    sess.update_info({"z": z})
    log.info(f"Updated Flywheel session info: z = {z}")


def first_dicom_from_zip(zfname: str) -> pydicom.Dataset:
    """Dicom header for first file in zip
    Read inplace via stream, without extracting zip."""

    # HACK: expect zip, but special case if input is dicom
    if not re.search(r".zip$", str(zfname)):
        log.warning("Not given a .zip, assuming file from single dicom acquisition?")
        return pydicom.dcmread(zfname)

    with ZipFile(zfname) as zf:
        for entry in zf.filelist:
            if entry.file_size > 0:
                with zf.open(entry.filename) as fh:
                    return pydicom.dcmread(fh)
    raise ValueError("No valid DICOM found in zip.")


def read_emails(config: dict) -> list[dict]:
    recips = config["recipients"]
    return [
        {"host": recips["host"], "from": recips["from"], "to": to}
        for to in recips["to"]
    ]


def get_label(fw, dest_id: str | None) -> str:
    """
    Use fw client to fetch dest_id subject label and creation time

    @param fw      Flywheel client
    @param dest_id FW DB id of acquisition file-curate is run on, like 6899c986fbeb05f0ba422e90
    @return label and created date concatenated"""
    if fw is None or dest_id is None:
        return ""

    if container := fw.get(dest_id):
        p = fw.get(container.parents.subject)
        # sesmod = str(fw.get(container.parents.session).get('timestamp'))
        # TODO: created timezone in Eastern
        return p.get("label") + "@" + str(container.get("created"))

    log.warning("No session for dest %s", dest_id)
    return ""


def main(zip_path: str, config_path: str, dest_id: str = None, client=None):
    """
    Run shim QC check and send email notifications.

    Parameters
    ----------
    zip_path : str
        Path to ZIP file containing DICOMs.
    config_path : str
        Path to toml with either:
          - new style [[scanner]] & [[emails]], or
          - old style [station_map], [z_thresholds], [recipients].
    """
    # Load + parse new/back-compat config
    config = load_toml_config(config_path)
    scanner_name_by_id, threshold_by_id, email_configs = parse_config(config)

    # Read first DICOM and extract Z
    dcm = first_dicom_from_zip(zip_path)
    z = read_z(dcm)

    # Map StationName -> display short name and threshold
    station_id = (getattr(dcm, "StationName", "") or "").strip() or "UNKNOWN"
    display_name = scanner_name_by_id.get(station_id, station_id)
    threshold = float(threshold_by_id.get(station_id, 10000.0))

    # Console line for logs
    print(f"# Z={z:.2f} from {display_name} (StationName={station_id})")

    # Build notification message
    msg = notify_message(display_name, z, threshold)

    # Optional: append session label if available (uses your existing get_label)
    try:
        if session_label := get_label(client, dest_id):
            msg += f"\nSession: {session_label}"
    except Exception as e:
        log.warning(f"Failed to retrieve session label for {dest_id}: {e}")

    print(msg)

    # Subject line (uses display_name, which is already short like P1/P2 if configured)
    emoji = "✅" if z >= threshold else "⛔"
    subject = f"{emoji} {display_name} z ShimQA {'okay' if emoji == '✅' else 'BAD'}"

    # Send emails (email_configs already expanded to per-recipient dicts)
    for entry in email_configs:
        try:
            send_email(
                subject=subject,
                body=msg,
                sender=entry["from"],
                recipient=entry["to"],
                host=entry["host"],
            )
        except Exception as e:
            log.warning(f"Failed to send to {entry.get('to')} via {entry.get('host')}: {e}")

class Curator(FileCurator):
    """
    Extend flywheels class to integrate with the file-curate gear.
    py:func:`Curator.curate_file` is launch point for file-curator when run as a gear.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None

    def curate_file(self, file_: Dict[str, Any]):
        """
        Start here! This is "main" analog when this file is script input to file-curate run as a gear.

        @param file_ is **dict** holding file curator (gear rule) info.
                     ["location"]["path"] is the dicom zip input file

        "additional-input-one" in get_input_path is
        whatever the user specifies AFTER specifying this python file (shim_notify.py).

        _file looks like
        .. code:

           {'hierarchy': {'id': '6899c986fbeb05f0ba422e90', 'type': 'acquisition'},
            'object': {'type': 'dicom', 'mimetype': 'application/zip', 'modality': 'MR', 'classification':.... },
            'location': {'path': '/flywheel/v0/input/file-input/1.3.12.2.1107.5.2.43.167046.2025081106355462484301088.0.0.0.dicom.zip', 'name': '1.3.12.2.1107.5.2.43.167046.2025081106355462484301088.0.0.0.dicom.zip'},
           'base': 'file'}
        """
        zip_path = file_["location"]["path"]
        config_path = self.context.get_input_path("additional-input-one")
        # dest_id = self.context.destination["id"] # this is where we're saving to
        acq_id = file_["hierarchy"][
            "id"
        ]  #: this is the object we are working on (zip file)
        main(zip_path, config_path, dest_id=acq_id, client=self.client)


#: run as a script to exercise code without having to upload to flywheel
#: when using with `dest_id` see export FLYWHEEL_API for changing site
if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())
    if len(sys.argv) not in [3, 4]:
        print(
            f"Usage: {sys.argv[0]} <dicom.zip> <shim_settings.toml> [flywheel_dest_id=6899c986fbeb05f0ba422e90]"
        )
        sys.exit(1)

    zip_path = sys.argv[1]
    config_path = sys.argv[2]
    dest_id = None
    client = None
    if len(sys.argv) == 4:
        print(f"Using new flywheel client for {dest_id}")
        dest_id = sys.argv[3]
        import flywheel

        client = flywheel.Client()

    main(zip_path, config_path, dest_id, client)
