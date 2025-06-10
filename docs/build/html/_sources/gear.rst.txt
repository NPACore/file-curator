Shim Notify Gear
================

The `shim_notify.py` script runs as the main entrypoint of the Flywheel gear.
It performs Z-shim quality checks on Siemens MRI data and notifies relevant users via email.

Each email recipient entry should include:

.. code-block:: toml

   [[recipients]]
   from = "scanner-alerts@example.com"
   to = "tech@example.com"
   host = "smtp.example.com"

Workflow summary
----------------

1. Extract the first DICOM file from the ZIP archive.
2. Parse Siemens CSA headers to extract the Z-shim offset.
3. Determine scanner type from `StationName`.
4. Compare Z value to scanner-specific threshold.
5. Notify recipients with pass/fail result.
6. Optionally update Flywheel session metadata (if run within a gear context).

Source Code Reference
---------------------

.. automodule:: shim_notify
   :members:
   :undoc-members:
   :show-inheritance:

