"""Simple script to create a plot from the first two columns of a CSV file.

This script includes a create_plots_and_save function that creates a plot and saves it.
"""

import json
import logging
import os
import sys

import pandas as pd

log = logging.getLogger("data_plotter")

try:
    import matplotlib.pyplot as plt
except ImportError:
    log.error("matplotlib is not installed. Please install it to create plots.")
    # exit
    sys.exit(1)


def create_plots_and_save(csv_file, output_folder, config_file=None):
    """Create the plots and save them to the specified folder.

    Args:
        csv_file (str): Path to the CSV file with the data.
        output_folder (str): Folder where the plots will be saved.
        config_file (str, optional): Path to the configuration file.
    """
    # Read the first two columns of the CSV file:
    try:
        data = pd.read_csv(csv_file, usecols=[0, 1])
        log.info("Successfully read the first two columns of %s", csv_file)
    except Exception as e:
        log.error(f"Failed to read the CSV file: {e}")
        return

    # Load the configuration file if provided
    config = {}
    if config_file:
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading configuration file: {e}")

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Generate plots based on the configuration or default behavior
    try:
        plt.figure(figsize=config.get("figure_size", (10, 6)))
        plt.plot(
            data.iloc[:, 0],
            data.iloc[:, 1],
            marker=config.get("marker", "o"),
            linestyle=config.get("linestyle", "-"),
        )
        plt.xlim(config.get("xlim", None))
        plt.xlabel(config.get("xlabel", "X-axis"))
        plt.ylim(config.get("ylim", None))
        plt.ylabel(config.get("ylabel", "Y-axis"))
        plt.title(config.get("title", "Plot of the first two columns"))
        if config.get("grid", False):
            plt.grid()
        plt.grid()
        output_path = os.path.join(
            output_folder, config.get("output_filename", "plot.png")
        )
        plt.savefig(output_path)
        log.info(f"Plot saved to {output_path}")
    except Exception as e:
        log.error(f"Failed to create the plot: {e}")
    finally:
        plt.close()
        log.info("Plot closed.")
