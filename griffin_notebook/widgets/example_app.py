# -*- coding: utf-8 -*-
#
# Copyright (c) Griffin Project Contributors


"""
Simple application for working with notebooks.

This is a stand-alone application showing how griffin_notebook can be used
outside Griffin. It is mainly meant for development and testing purposes,
but it can also serve as an example.
"""

# Standard library imports
import argparse
import logging
import sys

# Qt imports
import qdarkstyle
from qtpy.QtCore import QCoreApplication, Qt
from qtpy.QtQuick import QQuickWindow, QSGRendererInterface
from qtpy.QtWidgets import QAction, QApplication, QMainWindow

# Local imports
from griffin_notebook.utils.servermanager import ServerManager
from griffin_notebook.widgets.notebooktabwidget import NotebookTabWidget
from griffin_notebook.widgets.serverinfo import ServerInfoDialog


def use_software_rendering():
    """
    Instruct Qt to use software rendering.

    This is necessary for some buggy graphics drivers (e.g. nvidia).
    This function should be run before the QApplication is created.
    """
    QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    QQuickWindow.setSceneGraphBackend(QSGRendererInterface.Software)


class NotebookAppMainWindow(QMainWindow):
    """Main window for stand-alone notebook application."""

    def __init__(self, options):
        super().__init__()

        if options.dark:
            self.setStyleSheet(qdarkstyle.load_stylesheet_from_environment())

        self.server_manager = ServerManager(options.dark)
        QApplication.instance().aboutToQuit.connect(
            self.server_manager.shutdown_all_servers)

        self.tabwidget = NotebookTabWidget(
            self, self.server_manager, dark_theme=options.dark)

        if options.notebook:
            self.tabwidget.open_notebook(options.notebook)
        else:
            self.tabwidget.maybe_create_welcome_client()

        self.setCentralWidget(self.tabwidget)
        self._setup_menu()

    def view_servers(self):
        """Display server info."""
        dialog = ServerInfoDialog(self.server_manager.servers, parent=self)
        dialog.show()

    def _setup_menu(self):
        file_menu = self.menuBar().addMenu('File')

        new_action = QAction('New Notebook', self)
        new_action.triggered.connect(self.tabwidget.create_new_client)
        file_menu.addAction(new_action)

        open_action = QAction('Open Notebook...', self)
        open_action.triggered.connect(self.tabwidget.open_notebook)
        file_menu.addAction(open_action)

        save_action = QAction('Save Notebook', self)
        save_action.triggered.connect(
            lambda checked: self.tabwidget.save_notebook(
                self.tabwidget.currentWidget()))
        file_menu.addAction(save_action)

        saveas_action = QAction('Save As...', self)
        saveas_action.triggered.connect(self.tabwidget.save_as)
        file_menu.addAction(saveas_action)

        close_action = QAction('Close Notebook', self)
        close_action.triggered.connect(
            lambda checked: self.tabwidget.close_client(
                self.tabwidget.currentIndex()))
        file_menu.addAction(close_action)

        misc_menu = self.menuBar().addMenu('Misc')

        servers_action = QAction('View Servers...', self)
        servers_action.triggered.connect(self.view_servers)
        misc_menu.addAction(servers_action)


def main():
    """Execute example application."""
    use_software_rendering()
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    arguments = app.arguments()
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', nargs='*')
    parser.add_argument('--dark', action='store_true')
    result = parser.parse_args(arguments[1:])  # arguments[0] = program name
    window = NotebookAppMainWindow(result)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
