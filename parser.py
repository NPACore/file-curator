from typing import Tuple, Dict, Optional
from flywheel_gear_toolkit import GearToolkitContext
import flywheel


def parse_config(
    gear_context: GearToolkitContext,
) -> Tuple[str, flywheel.FileEntry, Dict[str, Optional[str]], Optional[str]]:
    """Parse gear config

    Args:
        gear_context (GearToolkitContext):

    Returns:
        Tuple[str, str, Dict[str, Optional[str]], Optional[str]]: 
            tuple containing:
                - (str) path to curator
                - (flywheel.FileEntry) input file
                - (Dict[str,Optional[str]]) Dictionary of optional additional inputs
                - (Optional[str]) optional requirements to install
    """

    curator_path = gear_context.get_input_path("curator")
    optional_requirements = None
    optional_requirements = gear_context.get_input_path("optional-requirements")

    file_input = gear_context.get_input("file-input")
    input_file_one = gear_context.get_input_path("additional-input-one")
    input_file_two = gear_context.get_input_path("additional-input-two")
    input_files = {
        "input_file_one": input_file_one,
        "input_file_two": input_file_two,
    }
    return curator_path, file_input, input_files, optional_requirements
