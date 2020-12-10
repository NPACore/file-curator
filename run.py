#!/usr/bin/env python
import logging
import parser

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import datatypes, install_requirements
from flywheel_hierarchy_curator.curate import get_curator

log = logging.getLogger(__name__)


def curate(
    context: GearToolkitContext,
    file_input: flywheel.FileEntry,
    curator_path: datatypes.PathLike,
    **kwargs,
) -> None: # pragma: no cover
    curator = get_curator(context, curator_path, **kwargs)

    curator.curate_container(file_input)


def main(gear_context: GearToolkitContext) -> None: # pragma: no cover
    (
        curator_path,
        file_input,
        optional_inputs,
        optional_requirements,
    ) = parser.parse_config(gear_context)

    if optional_requirements:
        log.info(f"Installing requirements from {optional_requirements}")
        install_requirements(optional_requirements)

    log.info(f"Curating {file_input.get('location').get('name')}")

    curate(
        gear_context,
        file_input,
        curator_path,
        write_report=gear_context.config.get("write_report"),
        **optional_inputs,
    )


if __name__ == "__main__": # pragma: no cover
    with GearToolkitContext() as gear_context:
        gear_context.init_logging(
            default_config_name=(
                "debug" if gear_context.config.get("verbose") else "info"
            )
        )
        main(gear_context)
