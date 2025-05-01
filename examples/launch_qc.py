"""
Launch mrrcqa gear with HPC tag via gear rule
"""

import logging
import random
import re
import zipfile
from pathlib import Path
from typing import Any, Dict

import pydicom
import flywheel
from flywheel_gear_toolkit.utils.curator import FileCurator
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter

log = logging.getLogger("launchHPC")
log.setLevel("DEBUG")

def launch_gear(fw, file_: flywheel.FileEntry):
    gear = fw.lookup("gears/mrrcqa")
    container = file_.parent
    log.info("gear %s:%s into parent contianer %s", gear.gear.name, gear.gear.version, container.label)

    inputs = {"phantom_dicom": file_}
    config = {"write_db": True}
    tags = ["mrrcqa", "hpc"]
    job_id = gear.run(tags=tags, config=config, inputs=inputs, destination=container)
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
        jobid = launch_gear(self.client, file_entity)
        log.info("launched %d", jobid)
