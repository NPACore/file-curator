"""
Launch mrrcqa gear with HPC tag via gear rule
"""

import logging
import re
from typing import Any, Dict

import flywheel
from flywheel_gear_toolkit.utils.curator import FileCurator
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter

log = logging.getLogger("launchHPC")
log.setLevel("DEBUG")


def launch_gear(fw, file_entity: flywheel.FileEntry) -> str:
    """
    Launch MRRC QA with "hpc" tag.
    .. warning::
      ``fw`` must be client bound to real user. gear rule's SYSTEM cannot POST to /jobs/new.

    :param fw: client
    :param file_entity: entity w/ files array that includes dicom zip
    :returns: jobid of new job
    """
    # log.info("input file: %s", file_entity)

    dcm = [f for f in file_entity.files if f.mimetype == "application/zip"]
    if len(dcm) != 1:
        raise Exception(f"Expect single dicom zip. got {len(dcm)}")
    file = dcm[0]

    gear = fw.lookup("gears/mrrcqa")
    log.info("gear %s:%s into %s", gear.gear.name, gear.gear.version, file_entity.label)

    inputs = {"phantom_dicom": file}
    config = {"write_db": True}
    tags = ["mrrcqa", "hpc"]
    job_id = gear.run(tags=tags, config=config, inputs=inputs, destination=file_entity)
    return job_id


def read_fernet_file(file_in: str) -> str:
    """
    Decrypt fernet encoded API key in binary file.

    .. warning::
       Fixed/hardcode encryption key.
       Anyone with access to fernet file and this code could decrypt.
       But at least the keys aren't exposed at rest.

    .. code:: python

       with open('/tmp/api.fernet','wb') as fh:
           fh.write(Fernet(b'Gl3otISIWwmlifJI5HlRB_JfScfyJuYPcH44s7XdVlI=').\
               encrypt('fw.mrrc.upmc.edu:...'.encode()))

    :param file_in: path to binary file with fernet encrypted key
    :returns: clear text API key
    """
    from cryptography.fernet import Fernet

    # insecure!! fixed key.
    key = Fernet(b"Gl3otISIWwmlifJI5HlRB_JfScfyJuYPcH44s7XdVlI=")

    with open(file_in, "rb") as fh:
        enc = fh.read()
    return key.decrypt(enc).decode()


class Curator(FileCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None

    def curate_file(self, file_: Dict[str, Any]):
        """
        Entrypoint for file-curate gear.
        :param file_: dict (not flywheel.FileEntry) of specified file
                      or file which triggered gear from a gear rule.
        """
        log.info("looking at %s", file_)
        name = file_["location"]["name"]
        if not re.search(r".dicom.zip$", name):
            log.info("file '%s' is not a dicom archive! not running!", name)
            return

        file_id = file_["hierarchy"]["id"]
        file_entity = self.client.get(file_id)
        if not file_entity:
            log.error("Bad file ID? %s", file_["hierarchy"]["id"])
            raise Exception("no file")

        #: when file-curator is run from gear rule, job is run as 'SYSTEM' and yeilds
        #: flywheel.rest.ApiException: (500) Reason: Must be at least user to run gear
        #: so provide option to get encrypted key from additional input
        api_key_file = self.context.get_input_path("additional-input-one")
        if api_key_file:
            api_key = read_fernet_file(api_key_file)
            fw = flywheel.Client(api_key)
        else:
            log.warning(
                "No additional file. Reusing api client of file-curate (okay if not gear rule)."
            )
            fw = self.client

        jobid = launch_gear(fw, file_entity)
        # Detail: [{'type': 'missing', 'loc': ['body', 'inputs', 'phantom_dicom', 'FileReference', 'name'], 'msg': 'Field required', 'input': {'type': 'acquisition', 'id': '680b674a5e18231e7a65fc0f'}}, {'type': 'missing', 'loc': ['body', 'inputs', 'phantom_dicom', 'FileVersion', 'file_id'], 'msg': 'Field required', 'input': {'type': 'acquisition', 'id': '680b674a5e18231e7a65fc0f'}}]
        log.info("launched %s", jobid)
