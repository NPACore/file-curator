"""A FileCurator script that creates a plot of the file being curated.

This curator applies a plotting script passed in a the additional-input-one input file
to the file being curated. Any custom plot configuration can be stored in the
additional-input-two input file. The curator calls the method create_plots_and_save in
the plotter script.

This plotting script should be a Python script with a function called
"create_plots_and_save" that takes three arguments:
1. The file with the data to be plotted
2. The output directory where the plot should be saved
3. The plot configuration (optional)

An example of a plotting script is provided in the examples/simple_plotter.py file.

The plot configuration can be a dictionary with any custom configuration needed by the
plotting script.

The script can create any number of plots and save them in the output directory.

Any modules needed by the plotting script should be included in the extra_packages list
in the Curator __init__ method.
"""

import importlib
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from flywheel_gear_toolkit.utils.curator import FileCurator

log = logging.getLogger("data_plotter")
log.setLevel("INFO")


class Curator(FileCurator):
    def __init__(self, **kwargs):
        """Initialize curator."""
        # Set gear context. Install and load any extra packages needed by the plotter
        # script:
        super().__init__(**kwargs, extra_packages=["matplotlib"])

        # Get the plotter script filepath.
        # We want it to be of type Path so later we can import it:
        self.plotter_script = Path(self.context.get_input_path("additional-input-one"))
        if not self.plotter_script:
            raise ValueError("No plotter script provided in additional-input-one")

        self.plot_config_file = self.context.get_input_path("additional-input-two")
        if not self.plot_config_file:
            log.info(
                "No plot configuration file provided in additional-input-two. Using "
                "default configuration."
            )

    def load_plotter_module(self):
        """Load the plotter module from the provided script."""
        # Dynamically import the plot function from the provided script
        module_name = self.plotter_script.stem
        spec = importlib.util.spec_from_file_location(module_name, self.plotter_script)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Ensure the plot function exists in the module
        if not hasattr(module, "create_plots_and_save"):
            raise AttributeError(
                f"The script {self.plotter_script} does not define a 'create_plots_and_save' function."
            )

        return module

    def curate_file(self, file_: Dict[str, Any]):
        """Curate a file by creating plots."""
        module = self.load_plotter_module()

        # Call the plot function with the required arguments
        data_file_path = file_.get("location", {}).get("path")
        if not data_file_path:
            raise ValueError(
                "The file dictionary does not contain a valid 'location.path'."
            )

        # Plot and save to the output directory:
        module.create_plots_and_save(
            data_file_path, self.context.output_dir, self.plot_config_file
        )
