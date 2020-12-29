from typing import Any, Dict, Optional, Tuple

import flywheel
from flywheel_gear_toolkit import GearToolkitContext


def parse_config(
    gear_context: GearToolkitContext,
) -> Tuple[str, Dict[str, Any], Dict[str, Optional[str]]]:
    """Parse gear config

    Args:
        gear_context (GearToolkitContext):

    Returns:
        Tuple[str, str, Dict[str, Optional[str]], Optional[str]]: 
            tuple containing:
                - (str) path to curator
                - (Dict[str,Any]) input file
                - (Dict[str,Optional[str]]) Dictionary of optional additional inputs
    """

    curator_path = gear_context.get_input_path("curator")

    file_input = gear_context.get_input("file-input")
    input_file_one = gear_context.get_input_path("additional-input-one")
    input_file_two = gear_context.get_input_path("additional-input-two")
    input_files = {
        "additional_input_one": input_file_one,
        "additional_input_two": input_file_two,
    }
    return curator_path, file_input, input_files 
