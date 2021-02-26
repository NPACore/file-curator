from unittest.mock import MagicMock

from flywheel_gear_toolkit import GearToolkitContext

from fw_gear_file_curator.parser import parse_config


def test_parse_config():
    gear_context = MagicMock(spec=GearToolkitContext)

    parse_config(gear_context)

    gear_context.get_input_path.call_count == 4
    gear_context.get_input.assert_called_once_with("file-input")
