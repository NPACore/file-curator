from parser import parse_config
from unittest.mock import MagicMock

import flywheel
import pytest
from flywheel_gear_toolkit import GearToolkitContext


def test_parse_config():
    gear_context = MagicMock(spec=GearToolkitContext)

    parse_config(gear_context)

    gear_context.get_input_path.call_count == 4
    gear_context.get_input.assert_called_once_with("file-input")
