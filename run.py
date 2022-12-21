#!/usr/bin/env python
import logging

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import datatypes
from flywheel_gear_toolkit.utils.curator import get_curator

from fw_gear_file_curator import parser

log = logging.getLogger(__name__)


def curate(
    context: GearToolkitContext,
    file_input: flywheel.FileEntry,
    curator_path: datatypes.PathLike,
    **kwargs,
) -> None:  # pragma: no cover
    curator = get_curator(context, curator_path, **kwargs)

    curator.curate_container(file_input)


def main(context: GearToolkitContext) -> None:  # pragma: no cover
    (
        curator_path,
        file_input,
        optional_inputs,
    ) = parser.parse_config(context)

    input_filename = file_input.get("location").get("name")
    log.info(f"Curating {input_filename}")

    curate(
        context,
        file_input,
        curator_path,
        **optional_inputs,
    )

    # update input file tag
    tag = context.config.get("tag")
    if tag:
        context.update_file_metadata(file_input, tags=tag)


if __name__ == "__main__":  # pragma: no cover
    with GearToolkitContext() as context:
        context.init_logging()
        main(context)
