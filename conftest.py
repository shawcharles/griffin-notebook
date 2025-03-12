# -*- coding: utf-8 -*-
#


#

"""Configuration file for Pytest."""

# Standard library imports
import os

# To activate/deactivate certain things in Griffin when running tests.
# NOTE: Please leave this before any other import here!!
os.environ['SPYDER_PYTEST'] = 'True'

# Third-party imports
import pytest


@pytest.fixture(autouse=True)
def reset_conf_before_test():
    from griffin.config.manager import CONF
    CONF.reset_to_defaults(notification=False)
