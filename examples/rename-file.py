"""A FileCuator script that renames a file based from the attributes of the
file parents"""
import logging
import sys
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
        file_o = acq.get_file(self.context.get_input_filename("file-input"))
        sub = self.context.client.get_subject(file_o.parents.get("subject"))
        ses = self.context.client.get_session(file_o.parents.get("session"))

        new_name = NEW_NAME.format(sub=sub, ses=ses, acq=acq, file=file_o)

        if acq.get_file(new_name):
            log.debug(
                f"File with same name in container. "
                f"Removing {new_name} from container."
            )
            acq.remove_file(new_name)

        self.client.move_file(
            file_o.file_id,
            {
                "container_reference": file_o.parent_ref,
                "name": new_name,
                "run_gear_rules": False,
            },
        )

        # so that the .metadata.json is using the updated name to update the file tag
        file_["location"]["name"] = new_name
