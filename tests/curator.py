import logging
from pathlib import Path
from typing import Dict, Any

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils.curator import FileCurator
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter


log = logging.getLogger(__name__)


class Curator(FileCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None
        if self.write_report:
            log.info("Initiating reporter")
            self.reporter = AggregatedReporter(
                output_path=(Path(self.context.output_dir) / "test.csv")
            )

    def curate_file(self, file_: Dict[str, Any]):
        if self.reporter:
            self.reporter.append_log(
                container_type="file", label=file_.get("location").get("name")
            )
