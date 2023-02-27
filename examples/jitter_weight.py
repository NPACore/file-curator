import logging
import random
import zipfile
from pathlib import Path
from typing import Any, Dict

import pydicom
from flywheel_gear_toolkit.utils.curator import FileCurator
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter

log = logging.getLogger("deidentify_patient_weight")
log.setLevel("DEBUG")


class Curator(FileCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None
        if self.write_report:
            log.info("Initiating reporter")
            self.reporter = AggregatedReporter(
                output_path=(Path(self.context.output_dir) / "out.csv")
            )

    def curate_file(self, file_: Dict[str, Any]):
        log.info(f"Curating file {file_.get('location').get('name')}")
        f_read_path = Path(file_.get("location").get("path"))
        f_write_path = Path(self.context.output_dir / f_read_path.name)
        work = Path(self.context.work_dir)

        # try:
        with zipfile.ZipFile(str(f_read_path), "r") as z_read:
            z_read.extractall(path=str(work))

        with zipfile.ZipFile(str(f_write_path), "w") as z_write:
            for dcm_path in Path(self.context.work_dir).glob("*"):
                if dcm_path.is_file():
                    try:
                        dcm = pydicom.dcmread(str(dcm_path))
                        # Randomly adjust patient weight for deidentify (Adding "jitter")
                        setattr(
                            dcm,
                            "PatientWeight",
                            (
                                (
                                    dcm.get("PatientWeight")
                                    if dcm.get("PatientWeight")
                                    else 50
                                )
                                + random.randint(-10, 10)
                            ),
                        )
                        dcm.save_as(str(dcm_path))
                        z_write.write(str(dcm_path), arcname=(dcm_path.name))
                    except Exception as e:
                        if self.reporter:
                            self.reporter.append_log(
                                err=str(e),
                                container_type="file",
                                label=file_.name,
                                search_key="",
                                resolved=False,
                                container_id=file_.id,
                                msg="",
                            )
                        else:
                            log.error(e)
