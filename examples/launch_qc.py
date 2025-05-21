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
    :param fw: client
    :param file_entity: entity w/ files array that includes dicom zip
    :return: jobid of new job
    """
    #log.info("input file: %s", file_entity)

    dcm = [f for f in file_entity.files if f.mimetype == 'application/zip']
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
        if not re.search(r'.dicom.zip$', name):
            log.info("file '%s' is not a dicom archive! not running!", name)
            return

        file_id = file_['hierarchy']['id']
        file_entity = self.client.get(file_id)
        if not file_entity:
            log.error("Bad file ID? %s", file_['hierarchy']['id'])
            raise Exception("no file")

        jobid = launch_gear(self.client, file_entity)
        # Detail: [{'type': 'missing', 'loc': ['body', 'inputs', 'phantom_dicom', 'FileReference', 'name'], 'msg': 'Field required', 'input': {'type': 'acquisition', 'id': '680b674a5e18231e7a65fc0f'}}, {'type': 'missing', 'loc': ['body', 'inputs', 'phantom_dicom', 'FileVersion', 'file_id'], 'msg': 'Field required', 'input': {'type': 'acquisition', 'id': '680b674a5e18231e7a65fc0f'}}]
        log.info("launched %s", jobid)
