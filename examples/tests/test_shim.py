import pytest
import shim_notify


def test_reademail():
    ex_toml = "shim-emails.toml.example"
    (addr_from, addr_to) = shim_notify.read_emails(ex_toml)
    assert addr_from == "foran@pitt.edu"


def test_z_zip():
    ex_zip = "tests/dcm.zip"
    dcm = shim_notify.first_dicom_from_zip(ex_zip)
    z = shim_notify.read_z(dcm)
    assert z == 11736.0


def test_station():
    ex_zip = "tests/dcm.zip"
    dcm = shim_notify.first_dicom_from_zip(ex_zip)
    pname = shim_notify.station_to_name(dcm.StationName)
    assert pname == "P3"
