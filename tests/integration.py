#!/usr/bin/env python
import logging

import pytest
import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import install_requirements, datatypes

from flywheel_hierarchy_curator.curate import get_curator
import run
from pathlib import Path
import os

from unittest.mock import MagicMock

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

