# File Curator
File curator is a utility gear that performs a user provided custom curation on a single file.

The primary usage of File Curator will be for gear rules.

## Usage

### Inputs

* __curator__: File container implementation of custom curator class, see below
* __file-input__: File to perform the curation on
* __additional-input-one__, __additional-input-two__, __additional-input-three__: Optional additional inputs to be provided.  For example a CSV of data could be passed in that the curator checks against in order to properly classify a file.
* __optional-requirements__: Optional requirements.txt file which will be programatically installed at gear run time

### Configuration
* __write-report__ (boolean, default False): Whether or not to upload a report of the actions taken.
* __verbose__ (boolean, default False): Include debug statements in output

### Extending the custom curator class

The `FileCurator` class is provided in the [flywheel_gear_toolkit](https://gear-toolkit.readthedocs.io/en/latest/utils.html#curator).

This class should be extended in order to define a custom curation script.

Example `curate.py` script which could be passed into the __curator__ input

```python
import logging
from pathlib import Path
from typing import Dict, Any
import pydicom

from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils.curator import FileCurator
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter

log = logging.getLogger(__name__)

class Curator(FileCurator):
    def __init__(self, **kwargs):
        # Set gear context, and read only flywheel Client in parent constructor
        super().__init__(**kwargs)

        self.reporter = None
        # If write_report option is passed in, set up a reporter
        if self.write_report:
            log.info("Initiating reporter")
            self.reporter = AggregatedReporter(
                output_path=(Path(self.context.output_dir) / "test.csv")
            )

    # Extend curate_file.  The input file will be passed into this method
    def curate_file(self, file_: Dict[str, Any]):
        """
         file_ format defined here: https://gitlab.com/flywheel-io/public/gears/-/tree/master/spec#the-input-configuration
        
        file_ : {
            'base': 'file',
            'location': {
                'path': '<path>',
                'name': '<file_name>'
            },
            'hierarchy': {
                'type': '<container_type>', 
                'name': '<file_name>'
            },
            "object" : {
                "info" : {},
                "mimetype" : "application/octet-stream",
                "tags" : [],
                "measurements" : [],
                "type" : "<file_type>",
                "modality" : None,
                "size" : <size>
            }
        }
        """
        container_type = file_.get('hierarchy').get('type')
        # Set up output metadata
        file_metadata = {}

        file_path = file_.get('location').get('path')
        label = file_.get('location').get('name')

        # update classification
        if file_.get('object').get('type') == 'dicom':
            file_metadata['classification'] = 'T1'
            
        if self.reporter:
            self.reporter.append_log(
                container_type="file", label=label, msg='updated classification'
            )

        #output metadata: https://gitlab.com/flywheel-io/public/gears/-/tree/master/spec#output-metadata
        metadata = {
            container_type: {
                'files': [file_metadata]
            }
        }
        out_file = Path(self.context.output_dir) / '.metadata.json'
        with open(outfile,'w') as out:
            json.dump(metadata, out)

        if self.reporter:
            self.reporter.append_log(
                container_type="file", label=label, msg='wrote_metadata'
            )

```
