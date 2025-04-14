# Data Plotting Curators

This folder contains Curators that can be run via the File Curator gear.

## Simple Data Plotter Curator

The `simple_data_plotter_curator.py` file is a simple example of how to write a curation
script to be used by the File Curator gear to plot data from a CSV file and save it as a
PNG file in Flywheel.

This example shows how you can even use install and use Python modules not included with
the File Curator gear by declaring them as `extra_packages` in the class `__init__`
method.

## Data Plotter Curator

The `data_plotter_curator.py` file shows a more advanced example of a file curator.

In the `simple_data_plotter_curator.py`, if you want to modify the plot, you would need
to modify the curator file and uploading it to the platform, potentially ending with
multiple versions of the same file. If you want to run a previous version, you would
have to restore it.

A way around it is to have this curator leverage the additional inputs that the File
Curator gear allows as optional arguments. This particular curator declares a generic
plotter curator which will load any custom plotting function (called
`create_plots_and_save`) defined in the Additional Input One. The curator allows the
user to pass additional configuration parameters in a JSON file passed to the job as
the Additional Input Two.

This way, the `data_plotter_curator` doesn't need to be modified and can be reused over
and over again in multiple different jobs, and the user just needs to create different
plotting file which customize the `create_plots_and_save` function. And, if you just
want to change the plot configuration (marker type, font size, etc.), you don't even
need to modify the plotting file, just use a different plot configuration file.
