Princess is a small module to run a Jupyter notebook containing Python code,
with two specific conditions:

- The notebook runs in the current Python environment (the one used to load
  Princess), regardless of the kernel name in its metadata.
- Text output from the notebook is displayed directly in your terminal - or
  wherever you redirect it - so you can follow the progress of the notebook.

Usage::

    python -m princess Notebook.ipynb

Options:

- ``--save`` and ``--save-as Result.ipynb`` to save the notebook after running.
- ``--discard-on-error`` cancels ``--save[-as]`` if an error occurs.
- ``--run-before before.py`` runs the code from the Python file in the kernel,
  before running the notebook. This can be used to set up things like logging
  to behave differently from when the notebook is run interactively.
- ``--on-error-resume-next`` ignores errors from running notebook code and
  continues with the next cell. This is usually not a good idea.

PRINCESS: Please Run IPython Notebook in the Current Environment with Stdout
and Stderr
