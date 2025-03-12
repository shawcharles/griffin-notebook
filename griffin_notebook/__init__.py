# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Griffin Project Contributors
#

# -----------------------------------------------------------------------------

"""Griffin Notebook plugin."""

# Local imports
from griffin_notebook.notebookplugin import NotebookPlugin as PLUGIN_CLASS
from griffin_notebook._version import __version__


# Connect to Jupyter
def _jupyter_server_extension_paths():
    return [{'module': 'griffin_notebook'}]


def _jupyter_server_extension_points():
    from griffin_notebook.server.main import GriffinNotebookApp

    return [{'module': 'griffin_notebook', 'app': GriffinNotebookApp}]


def _jupyter_labextension_paths():
    return [{'src': 'labextension', 'dest': '@griffin-notebook/lab-extension'}]


PLUGIN_CLASS
