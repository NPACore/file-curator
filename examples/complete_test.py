"""
For gear rule. Trigger on single file, but look to parent session.
check all nifti files and tag input file with 'complete' if session file criteria are met
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

log = logging.getLogger("deidentify_patient_weight")
log.setLevel("DEBUG")


def check_complete(files) -> bool:
    """
    Is the file list complete?
    :param files: file names
    :return: True if have all expected files
    """
    expected = {r'mprage': 1, r'reward': 2, r'rest': 1}
    complete = []
    cnt = {r: 0 for r in expected}
    for fname in files:
        for rgx, ecnt in expected.items():
            if not re.search(rgx, fname, flags=re.IGNORECASE):
                continue
            cnt[rgx] += 1
            if cnt[rgx] == ecnt:
                complete.append(rgx)
                break
    log.info("counts %s; complete: %s", cnt, complete)
    return len(complete) == len(expected)


class Curator(FileCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None

    def curate_file(self, file_: Dict[str, Any]):
        # file_ is not flywheel.FileEntry #
        log.info("file struct: %s", file_)
        log.info("client: %s", self.client)

        file_id = file_['hierarchy']['id']
        file_entity = self.client.get(file_id)
        ses = file_entity.parents.session
        ses_acq = self.client.get(ses).acquisitions()
        files = [f.name
                 for a in ses_acq
                 for f in a.files 
                 if re.search('nii.gz$', f.name)]

        log.info("session has files: %s", files)
        if check_complete(files):
            log.info("complete! adding tag")
            file_entity.add_tag('complete')
        else:
            log.info("not yet complete")
