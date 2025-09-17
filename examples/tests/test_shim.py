# examples/tests/test_shim.py
from contextlib import contextmanager
import os.path
import pathlib
import pytest
import shim_notify
from zipfile import ZipFile

HERE = pathlib.Path(__file__).parent
CONFIG_NEW = HERE.parent / "shim_settings.toml"
EX_ZIP = HERE / "dcm.zip"


@contextmanager
def temporary_override(module, attr_name, new_value):
    """
    Temporarily replace `module.attr_name` with `new_value` during the 'with' block.
    Always restores the original value afterward.
    """
    original = getattr(module, attr_name)
    setattr(module, attr_name, new_value)
    try:
        yield
    finally:
        setattr(module, attr_name, original)


def test_load_and_parse_config_new_style():
    cfg = shim_notify.load_toml_config(str(CONFIG_NEW))
    scanner_name_by_id, threshold_by_id, email_entries = shim_notify.parse_config(cfg)

    # Emails expanded per recipient
    assert isinstance(email_entries, list) and len(email_entries) >= 1
    to_emails = {e["to"] for e in email_entries}
    assert "flywheelgearlist@list.pitt.edu" in to_emails

    # Scanner short names
    assert scanner_name_by_id["MRC67078"] == "P1"
    assert scanner_name_by_id["AWP167046"] == "P2"
    assert scanner_name_by_id["MRC35073"] == "P3"

    # Thresholds (tolerate float rounding)
    assert pytest.approx(threshold_by_id["MRC67078"], rel=1e-9) == 9931.513661
    assert pytest.approx(threshold_by_id["AWP167046"], rel=1e-9) == 4505.258657
    assert pytest.approx(threshold_by_id["MRC35073"], rel=1e-9) == 11652.571269


def test_read_z_zip_and_station_mapping():
    dcm = shim_notify.first_dicom_from_zip(str(EX_ZIP))
    z = shim_notify.read_z(dcm)
    assert z == 11736.0

    # Map StationName via new-style config
    cfg = shim_notify.load_toml_config(str(CONFIG_NEW))
    scanner_name_by_id, threshold_by_id, _ = shim_notify.parse_config(cfg)

    station_id = (getattr(dcm, "StationName", "") or "").strip() or "UNKNOWN"
    assert scanner_name_by_id[station_id] == "P3"
    assert threshold_by_id[station_id] > 0


def test_notify_message_formatting():
    ok_msg = shim_notify.notify_message("P3", 12000.0, 11652.571269)
    bad_msg = shim_notify.notify_message("P3", 10000.0, 11652.571269)
    assert "✅" in ok_msg and "okay" in ok_msg.lower()
    assert "⛔" in bad_msg and "bad" in bad_msg.lower()


def test_main_with_overrides():
    """
    Run main() with sample ZIP + new TOML, but override side-effectful
    functions so no email or Flywheel calls occur.
    """
    sent = []

    def fake_send_email(subject, body, sender, recipient, host="localhost"):
        sent.append(
            {
                "subject": subject,
                "body": body,
                "sender": sender,
                "recipient": recipient,
                "host": host,
            }
        )

    def fake_get_label(_fw, _dest_id):
        return ""  # no session label appended

    # Override send_email and get_label only within this block
    with temporary_override(shim_notify, "send_email", fake_send_email), \
         temporary_override(shim_notify, "get_label", fake_get_label):
        shim_notify.main(str(EX_ZIP), str(CONFIG_NEW), dest_id=None, client=None)

    # Validate emails were attempted and subject/body reflect pass/fail for P3
    assert len(sent) >= 1
    subj = sent[0]["subject"]
    body = sent[0]["body"]

    # z=11736 with P3 threshold 11652.571269 ⇒ pass
    assert subj.startswith("✅ P3 z ShimQA")
    assert "P3" in body and "okay" in body.lower()


def test_first_dicom_from_zip(tmp_path):
    "Check reading first dicom handles zip and dcm"
    ziphead = shim_notify.first_dicom_from_zip("tests/dcm.zip")
    inzippath = "PRISMA3QA2024/PRISMA3QA.MR.QA_PRISMA3QA.0003.0001.2024.08.09.18.15.49.154822.1380215093.IMA"
    with ZipFile(EX_ZIP) as zf:
        zf.extract(inzippath, tmp_path)
    dcmhead = shim_notify.first_dicom_from_zip(tmp_path / inzippath)

    assert ziphead is not None
    assert dcmhead is not None

    # might as well confirm both headers are the same agains the actual value
    z = shim_notify.read_z(ziphead)
    assert z == 11736.0
    assert z == shim_notify.read_z(dcmhead)
