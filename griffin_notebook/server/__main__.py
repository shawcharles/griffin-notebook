# Copyright (c) Jupyter Development Team, Griffin Project Contributors.
# Distributed under the terms of the Modified BSD License.

"""CLI entry point for Griffin Notebook server."""

import sys

from griffin_notebook.server.main import main

sys.exit(main())
