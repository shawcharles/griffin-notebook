# -*- coding: utf-8 -*-
#


#

"""Tests for plugin config dialog."""

from unittest.mock import MagicMock

# Test library imports
import pytest
from qtpy.QtWidgets import QMainWindow

# Local imports
from griffin.api.plugin_registration._confpage import PluginsConfigPage
from griffin.api.plugin_registration.registry import PLUGIN_REGISTRY
from griffin_notebook.notebookplugin import NotebookPlugin


class MainWindowMock(QMainWindow):
    register_shortcut = MagicMock()
    editor = MagicMock()

    def __getattr__(self, attr):
        return MagicMock()


@pytest.mark.parametrize(
    'config_dialog',
    # [[MainWindowMock, [ConfigPlugins], [Plugins]]]
    [[MainWindowMock, [], [NotebookPlugin]]],
    indirect=True)
def test_config_dialog(config_dialog):
    # Check that Notebook config page works
    configpage = config_dialog.get_page()
    assert configpage
    configpage.save_to_conf()

    # Check that Plugins config page works with notebook plugin
    # Regression test for griffin-ide/griffin-notebook#470
    PLUGIN_REGISTRY.set_all_internal_plugins(
        {NotebookPlugin.NAME: (NotebookPlugin.NAME, NotebookPlugin)}
    )
    plugins_config_page = PluginsConfigPage(PLUGIN_REGISTRY, config_dialog)
    plugins_config_page.initialize()
