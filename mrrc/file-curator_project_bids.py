#! /usr/bin/env python3
"""Run file-curator on project "bids"

    This script was created to run Job ID 6808ecc6188d64648eb3910e
    In project "flywheel/bids"
    On Flywheel Instance https://fw.mrrc.upmc.edu/api
"""

import os
import argparse
from datetime import datetime


import flywheel


input_files = {
    "curator": {"container_path": "flywheel/bids", "location_name": "complete_test.py"},
    "file-input": {
        "container_path": "flywheel/bids/bids-test/bids-test/1 - " "localizer",
        "location_name": "1_localizer_dicom_zi_localizer_20241018080815_1_i00001.nii.gz",
    },
}


def main(fw):
    gear = fw.lookup("gears/file-curator")
    print("gear.gear.version in original job was = 0.4.1")
    print(f"gear.gear.version now = {gear.gear.version}")
    print("destination_id = 67fe760bf029d0e4ed7d8151")
    print("destination type is: project")
    destination = fw.lookup("flywheel/bids")

    inputs = dict()
    for key, val in input_files.items():
        if val["container_path"][:8] == "analysis":
            path = val["container_path"][9:]
            parent_of_analysis = fw.lookup(path)
            # find analysis that has the right file
            analyses = parent_of_analysis.reload().analyses
            for analysis in analyses:
                for file in analysis.files:
                    if file.name == val["location_name"]:
                        container = analysis
        else:
            container = fw.lookup(val["container_path"])
        inputs[key] = container.get_file(val["location_name"])

    config = {"debug": False, "tag": ""}

    tags = ["file-curator"]

    job_id = gear.run(tags=tags, config=config, inputs=inputs, destination=destination, priority="high")
    print(f"job_id = {job_id}")
    return job_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    fw = flywheel.Client("")
    print(fw.get_config().site.api_url)

    analysis_id = main(fw)

    os.sys.exit(0)
