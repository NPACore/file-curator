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


def main(gear_context: GearToolkitContext) -> None:  # pragma: no cover
    (
        curator_path,
        file_input,
        optional_inputs,
    ) = parser.parse_config(gear_context)

    log.info(f"Curating {file_input.get('location').get('name')}")

    curate(
        gear_context,
        file_input,
        curator_path,
        **optional_inputs,
    )


if __name__ == "__main__":  # pragma: no cover
    with GearToolkitContext() as gear_context:
        gear_context.init_logging()
        main(gear_context)
