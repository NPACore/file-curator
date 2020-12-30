#!/usr/bin/env python
import logging
import os
from pathlib import Path
from unittest.mock import MagicMock

import flywheel
import pytest
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import datatypes, install_requirements
from flywheel_gear_toolkit.utils.curator import get_curator

import run

GROUP = "scien"
PROJECT = "Nate-BIDS-test"
OUTPUT = "/tmp/"
CURATOR = (Path(__file__).parents[0] / "curator.py").resolve()


@pytest.mark.skipif(
    not os.environ.get("api_key"), reason="Only meant for local testing"
)
def test_file_curator(mocker):
    fw = flywheel.Client(os.environ.get("api_key"))
    proj = fw.lookup(f"{GROUP}/{PROJECT}")

    file = {"location": {"name": proj.files[0].name}}

    parser_mock = mocker.patch("run.parser.parse_config")
    parser_mock.return_value = (str(CURATOR), file, {}, None)

    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.output_dir = OUTPUT

    run.main(gear_context)
