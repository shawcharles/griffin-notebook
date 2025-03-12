# -*- coding: utf-8 -*-
#
# Copyright (c) Griffin Project Contributors


"""Griffin configuration page for notebook plugin."""

# Qt imports
from qtpy.QtWidgets import QGridLayout, QGroupBox, QVBoxLayout

# Griffin imports
from griffin.api.preferences import PluginConfigPage

# Local imports
from griffin_notebook.utils.localization import _


class NotebookConfigPage(PluginConfigPage):
    """Widget with configuration options for notebook plugin."""

    def setup_page(self):
        """Fill configuration page with widgets."""
        themes = ['Same as Griffin', 'Light', 'Dark']
        theme_choices = list(zip(themes,
                                 [theme.lower() for theme in themes]))
        theme_combo = self.create_combobox(
            _('Notebook theme'), theme_choices, 'theme', restart=True)

        interface_layout = QGridLayout()
        interface_layout.addWidget(theme_combo.label, 0, 0)
        interface_layout.addWidget(theme_combo.combobox, 0, 1)
        interface_group = QGroupBox(_('Interface'))
        interface_group.setLayout(interface_layout)

        vlayout = QVBoxLayout()
        vlayout.addWidget(interface_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)
