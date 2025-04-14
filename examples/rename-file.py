"""A FileCurator script that renames a file based from the attributes of the
file parents.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from flywheel_gear_toolkit.utils.curator import FileCurator

log = logging.getLogger("deidentify_patient_weight")
log.setLevel("DEBUG")


# An example of using the format method to create a new name
NEW_NAME = "{sub.label}-{ses.label}-{acq.label}.json"


class Curator(FileCurator):
    def curate_file(self, file_: Dict[str, Any]):
        if file_.get("hierarchy").get("type") != "acquisition":
            log.error(
                f"File {file_.get('location').get('name')} is not in an acquisition"
            )
            sys.exit(1)

        log.info(f"Renaming file {file_.get('location').get('name')}")

        acq = self.context.get_container_from_ref(file_.get("hierarchy"))
        filename = self.context.get_input_filename("file-input")
        file_o = acq.get_file(filename)
        sub = self.context.client.get_subject(file_o.parents.get("subject"))
        ses = self.context.client.get_session(file_o.parents.get("session"))

        new_name = NEW_NAME.format(sub=sub, ses=ses, acq=acq, file=file_o)
        log.debug(f"File will be renamed as {new_name}")

        if acq.get_file(new_name):
            input_file_path = Path(self.context.get_input_path("file-input"))
            log.debug(
                f"Renaming {input_file_path} to {str(input_file_path.parent / new_name)}"
            )
            os.rename(input_file_path, input_file_path.parent / new_name)
            log.debug(f"Deleting {filename}")
            acq.delete_file(filename)
            log.debug(f"Uploading {str(input_file_path.parent / new_name)}")
            acq.upload_file(str(input_file_path.parent / new_name))
        else:
            self.client.move_file(
                file_o.file_id,
                {
                    "container_reference": file_o.parent_ref,
                    "name": new_name,
                    "run_gear_rules": False,
                },
            )

        file_["location"]["name"] = new_name
