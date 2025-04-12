"""A FileCurator script that creates a plot of the file being curated.

This curator grabs the first two columns of a CSV file and creates a plot of the data.
The plot is saved in the output directory of the gear.

When you need to use a package that is not included with the gear, you need to first
install it by passing the "extra_packages" argument to the Curator class initializer
(see below).  After that, your "plot" method (or any other function called by it) can
import that package.
"""

import logging
import os
from typing import Any, Dict

import pandas as pd
from flywheel_gear_toolkit.utils.curator import FileCurator

log = logging.getLogger("data_plotter")
log.setLevel("INFO")


class Curator(FileCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, extra_packages=["matplotlib"])

    def curate_file(self, file_: Dict[str, Any]):
        """Create a plot of the file being curated.

        This method checks that the input file is a CSV file, and if so, it grabs the
        first two columns and creates a plot of the data. The plot is saved in the
        output directory of the gear.

        Args:
            file_ (Dict[str, Any]): The file being curated.
        """
        file_path = file_.get("location", {}).get("path", "")
        # Check if the file is a CSV file
        if not file_path.endswith(".csv"):
            log.warning("The file is not a CSV file. Skipping.")
            return

        # Read the first two columns of the CSV file:
        try:
            data = pd.read_csv(file_path, usecols=[0, 1])
            log.info("Successfully read the first two columns of %s", file_path)
        except Exception as e:
            log.error(f"Failed to read the CSV file: {e}")
            return

        # Create a plot of the data:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            log.error("matplotlib is not installed. Please install it to create plots.")
            return

        try:
            plt.figure(figsize=(10, 5))
            plt.plot(data.iloc[:, 0], data.iloc[:, 1], marker="o")
            plt.xlabel("X-axis")
            plt.ylabel("Y-axis")
            plt.title("Plot of the first two columns of the CSV file")
            plt.grid()
            output_path = os.path.join(self.context.output_dir, "plot.png")
            plt.savefig(output_path)
            log.info(f"Plot saved to {output_path}")
        except Exception as e:
            log.error(f"Failed to create the plot: {e}")
        finally:
            plt.close()
            log.info("Plot closed.")
