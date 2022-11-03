# File Curator

File curator is a utility gear that performs a user provided custom curation script on
a single file.

## Usage

### Inputs

* __curator__: A python script implementing a FileCurator class. See below.
* __file-input__: File to curate.
* __additional-input-one__, __additional-input-two__, __additional-input-three__:
  Optional additional inputs to be provided.  For example a CSV of data could be
  passed in that the curator checks against in order to properly classify a file.

### Configuration

* __debug__ (boolean, default `False`): Include debug statements in output.
* __tag__ (string, default `""`): The tag to be added on input file upon run completion.

## Customization

### Extending the custom curator class

The `FileCurator` class is provided in the [flywheel_gear_toolkit](https://gear-toolkit.readthedocs.io/en/latest/utils.html#curator).

This class should be extended in order to define a custom curation script.

Example `curate.py` script which could be passed as the __curator__ input.  This
example script trivially sets the file classification 'Measurement' key to 'T1'

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

    # Define curate_file.  The input file will be passed into this method
    def curate_file(self, file_: Dict[str, Any]):
        """Sets file measurement to T1.

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
            file_metadata['classification'] = {
                'Measurement':['T1']
            }
        # Specify which file to update by passing in file name
        file_metadata['name'] = label

        #output metadata: https://gitlab.com/flywheel-io/public/gears/-/tree/master/spec#output-metadata
        metadata = {
            container_type: {
                'files': [file_metadata]
            }
        }
        out_file = Path(self.context.output_dir) / '.metadata.json'
        with open(outfile,'w') as out:
            json.dump(metadata, out)

        log.info('Wrote metadata')
```

### Adding extra dependencies

The file-curator gear comes with the following python packages installed:

* lxml
* pandas
* nibabel
* Pillow
* piexif
* pydicom
* pypng
* flywheel-gear-toolkit
__Note__: See package versions in [./pyproject.toml](pyproject.toml)

If you need other dependencies that aren't installed by default.  The gear-toolkit provides
an interface to programmatically install dependencies.  You can specify a `requirements.txt`
file as one of the additional inputs then install them your `Curator.__init__` method:

```python
from flywheel_gear_toolkit.utils import install_requirements
...
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        install_requirements(self.additional_input_one)
```
