#!/usr/bin/env python3
"""
Check shim values for failure.
Notify good/bad shim regardless.
"""

import os
import re
import sys

# tomllib is new in python 3.11. have 3.10 in guix.
# what does 'flywheel/python-gdcm' use?
try:
    import tomllib as toml
except:
    import toml
import warnings
from typing import Any, Dict
from zipfile import ZipFile

import flywheel
import pydicom
from flywheel_gear_toolkit.utils.curator import FileCurator

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    # UserWarning: The DICOM readers are highly experimental...
    from nibabel.nicom import csareader


def station_to_name(station_id: str) -> str:
    # TODO: fill this out. pull PrismaXQA examples and lookt at
    # dcm.StationName
    stations = {
        "MRC35073": "P3",
    }
    station = stations.get(station_id) or station_id
    return station


def notify_message(scanner: str, z: float):
    """ """
    # TODO: find failing values on rad.pitt.edu/wiki
    #: shim values higher than this are okay
    low_threshold = 10000

    thres_str = "!!!ERROR!!! bAD SHIM\n" if z < low_threshold else "value okay. "

    return f"{thres_str}{scanner}: z={z} (thres={low_threshold})"


def notify(msg: str, faddr: str, taddr: str, host: any):
    """
    Send an email notificiation
    :param msg: message to send
    :param faddr: form address like xxx@yyyy.
                  will connect to server yyyy
    :param taddr: address to send to
    :param host: smtp host. if none, pull form faddr

    Note on infractucture
    on pitt's ewi, sending from and to the same pitt email works in php
    mail($to,$subject,$message,$headers);
    """
    from smtplib import SMTP

    if host is None:
        host = re.sub(".*@", "", faddr)
    host = 'localhost'
    print(f"connecting to {host}")
    with SMTP(host) as srv:
        print(f"connected")
        srv.noop()
        srv.set_debuglevel(1)
        srv.sendmail(faddr, taddr, msg)
    #os.system('printf "From: foran@pitt.edu\nTo: foran@pitt.edu\nSubject: Test from zeus\n\nEOM" | sendmail -t foran@pitt.edu')


def read_z(dcm) -> float:
    """
    Read lOffsetZ from CSA header
    This assumes a lot about the dicoms header! likely to fail on new data
    :param dcm: dicom from pydicom
    :return: Z shim value as a float
    """
    csa = dcm.get((0x0029, 0x1020))
    csa_s = csareader.read(csa.value)
    asccov = csa_s["tags"]["MrPhoenixProtocol"]["items"][0]
    reg = re.compile(r"sGRADSPEC.asGPAData\[0\].lOffsetZ\s*=\s*([^\s]+)")
    return float(reg.search(asccov).group(1))


def update_db(fw, dest_id, z: float):
    """
    Flywheel SDK gear style DB update: write snr peak value to sess.info.snr
    Requires write permission when used as a gear rule.

    :param context: implicit context when running as a gear
    :param z: z shim parameter
    """
    # fw = context.client
    # cid = context.destination['id']
    container = fw.get(dest_id)
    if container is None:
        raise Exception(f"no containder '{cid}'")

    sess = fw.get(container.parents.session)
    info = {"z": z}
    # 20250422 - confirmed updateding info
    #            does not clear keys that are not specified
    #            will only add z, will not remove eg. 'shims'
    sess.update_info(info)
    print(f"updated sess db: {info}")


def first_dicom_from_zip(zfname) -> pydicom.dataset.FileDataset:
    """
    read the first non-zero (hopefully dicom) file from a zip file
    :param zfname: zip file path
    :return: dicom object
    """
    with ZipFile(zfname) as zf:
        first = [x for x in zf.filelist if x.file_size > 0][0]
        with zf.open(first.filename) as dcm_fh:
            dcm = pydicom.dcmread(dcm_fh)
    return dcm


def main(input_path, from_addr, to_addr):
    """
    Get only the z shim value. Optionally, email state
    Maybe eventually also update FW DB
    """
    dcm = first_dicom_from_zip(input_path)
    z = read_z(dcm)
    scanner = station_to_name(dcm.StationName)
    print(f"# {z} {scanner}")

    # update_db(fw, )

    if from_addr:
        msg = notify_message(scanner, z)
        notify(msg, from_addr, to_addr)


def read_emails(toml_path) -> tuple[str, str]:
    """
    read TOML file to extact from and to. only from is required

    from = "foran@pitt.edu"
    to = "foran@pitt.edu"
    host = "smtp.host.edu"
    """
    # tomllib wants 'rb' not 'r'?
    with open(toml_path, "r") as toml_fh:
        emails = toml.load(toml_fh)
    return (emails["from"], emails.get("to") or emails["from"], emails.get("host"))


class Curator(FileCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None

    def curate_file(self, file_: Dict[str, Any]):
        input_path = file_["location"]["path"]
        toml_file = self.context.get_input_path("additional-input-one")
        from_addr, to_addr, host = read_emails(toml_file)
        main(input_path, from_addr, from_addr, host)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"USAGE: {sys.argv[0]} dicom.zip emails.toml")
        sys.exit(1)
    input_path = sys.argv[1]
    from_addr, to_addr = read_emails(sys.argv[2])
    main(input_path, from_addr, from_addr)
