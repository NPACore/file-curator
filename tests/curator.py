import logging
from pathlib import Path

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils.curator import FileCurator
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter


log = logging.getLogger(__name__)


class Curator(FileCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        log.info("Initiating reporter")
        if self.write_report:
            self.reporter = AggregatedReporter(
                output_path=(Path(self.context.output_dir) / "test.csv")
            )

    def curate_file(self, file_: flywheel.FileEntry):
        if self.reporter:
            self.reporter.append_log(
                container_type=file_.container_type, container_label=file_.name
            )
