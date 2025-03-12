# -*- coding: utf-8 -*-
#
# Copyright (c) Griffin Project Contributors


"""Qt widgets for the notebook."""

# Standard library imports
import json
import logging
import os
import os.path as osp
from string import Template
import sys

# Third-party imports
from jupyter_server.utils import url_path_join, url_escape
import qstylizer
from qtpy.QtCore import QEvent, QUrl, Qt, Signal
from qtpy.QtGui import QColor, QFontMetrics, QFont
from qtpy.QtWebEngineWidgets import (QWebEnginePage, QWebEngineSettings,
                                     QWebEngineView, WEBENGINE)
from qtpy.QtWidgets import (QApplication, QMenu, QFrame, QVBoxLayout,
                            QMessageBox)
import requests

# Griffin imports
from griffin.config.base import get_module_source_path
from griffin.utils import sourcecode
from griffin.utils.image_path_manager import get_image_path
from griffin.utils.qthelpers import add_actions
from griffin.utils.palette import GriffinPalette
from griffin.widgets.findreplace import FindReplace

# Local imports
from griffin_notebook.config import CONF_SECTION
from griffin_notebook.utils.localization import _
from griffin_notebook.widgets.dom import DOMWidget

# -----------------------------------------------------------------------------
# Templates
# -----------------------------------------------------------------------------
# Using the same css file from the Help plugin for now. Maybe
# later it'll be a good idea to create a new one.

PLUGINS_PATH = get_module_source_path('griffin', 'plugins')
TEMPLATES_PATH = osp.join(
    PLUGINS_PATH, 'ipythonconsole', 'assets', 'templates')

BLANK = open(osp.join(TEMPLATES_PATH, 'blank.html')).read()
LOADING = open(osp.join(TEMPLATES_PATH, 'loading.html')).read()
KERNEL_ERROR = open(osp.join(TEMPLATES_PATH, 'kernel_error.html')).read()

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Widgets
# -----------------------------------------------------------------------------
class WebViewInBrowser(QWebEngineView):
    """
    WebView which opens document in an external browser.

    This is a subclass of QWebEngineView, which as soon as the URL is set,
    opens the web page in an external browser and closes itself. It is used
    in NotebookWidget to open links.
    """

    def __init__(self, parent):
        """Construct object."""
        super().__init__(parent)
        self.urlChanged.connect(self.open_in_browser)

    def open_in_browser(self, url):
        """
        Open web page in external browser and close self.

        Parameters
        ----------
        url : QUrl
            URL of web page to open in browser
        """
        import webbrowser
        try:
            webbrowser.open(url.toString())
        except ValueError:
            # See: griffin-ide/griffin#9849
            pass
        self.stop()
        self.close()


class NotebookWidget(DOMWidget):
    """WebView widget for notebooks."""

    sig_focus_in_event = Signal()
    """
    This signal is emitted when the widget receives focus.
    """

    sig_focus_out_event = Signal()
    """
    This signal is emitted when the widget loses focus.
    """

    def __init__(self, parent, actions=None):
        """
        Constructor.

        Parameters
        ----------
        parent : QWidget
            Parent of the widget under construction.
        actions : list of (QAction or QMenu or None) or None, optional
            Actions to be added to the context menu of the widget under
            construction. The default is None, meaning that no actions
            will be added.
        """
        super().__init__(parent)
        self.CONTEXT_NAME = str(id(self))
        self.setup()
        self.actions = actions

        # Path for css files in Griffin according to the interface theme set by
        # the user (i.e. dark or light).
        self.css_path = self.get_conf('css_path', section='appearance')

        # Set default background color.
        self.page().setBackgroundColor(
            QColor(GriffinPalette.COLOR_BACKGROUND_1)
        )

    def contextMenuEvent(self, event):
        """
        Handle context menu events.

        This overrides WebView.contextMenuEvent() in order to add the
        actions in `self.actions` and remove the Back and Forward actions
        which have no meaning for the notebook widget.

        If Shift is pressed, then instead display the standard Qt context menu,
        per gh:griffin-ide/griffin-notebook#279

        Parameters
        ----------
        event : QContextMenuEvent
            The context menu event that needs to be handled.
        """
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            return QWebEngineView.contextMenuEvent(self, event)

        if self.actions is None:
            actions = []
        else:
            actions = self.actions + [None]

        actions += [
            self.pageAction(QWebEnginePage.SelectAll),
            self.pageAction(QWebEnginePage.Copy),
            None,
            self.zoom_in_action,
            self.zoom_out_action]

        if not WEBENGINE:
            settings = self.page().settings()
            settings.setAttribute(QWebEngineSettings.DeveloperExtrasEnabled,
                                  True)
            actions += [None, self.pageAction(QWebEnginePage.InspectElement)]

        menu = QMenu(self)
        add_actions(menu, actions)
        menu.popup(event.globalPos())
        event.accept()

    def _set_info(self, html):
        """Set informational html with css from local path."""
        self.setHtml(html, QUrl.fromLocalFile(self.css_path))

    def show_blank(self):
        """Show a blank page."""
        blank_template = Template(BLANK)
        page = blank_template.substitute(css_path=self.css_path)
        self._set_info(page)

    def show_kernel_error(self, error):
        """Show kernel initialization errors."""
        # Remove unneeded blank lines at the beginning
        eol = sourcecode.get_eol_chars(error)
        if eol:
            error = error.replace(eol, '<br>')
        # Don't break lines in hyphens
        # From http://stackoverflow.com/q/7691569/438386
        error = error.replace('-', '&#8209')

        message = _("An error occurred while starting the kernel")
        kernel_error_template = Template(KERNEL_ERROR)
        page = kernel_error_template.substitute(css_path=self.css_path,
                                                message=message,
                                                error=error)
        self._set_info(page)

    def show_loading_page(self):
        """Show a loading animation while the kernel is starting."""
        loading_template = Template(LOADING)
        loading_img = get_image_path('loading_sprites.png')
        if os.name == 'nt':
            loading_img = loading_img.replace('\\', '/')
        message = _("Connecting to kernel...")
        page = loading_template.substitute(css_path=self.css_path,
                                           loading_img=loading_img,
                                           message=message)
        self._set_info(page)

    def show_message(self, page):
        """Show a message page with the given .html file."""
        self.setHtml(page)

    def createWindow(self, webWindowType):
        """
        Create new browser window.

        This function is called by Qt if the user clicks on a link in the
        notebook. The goal is to open the web page in an external browser.
        To that end, we create and return an object which will open the browser
        when Qt sets the URL.
        """
        return WebViewInBrowser(self.parent())

    def eventFilter(self, widget, event):
        """
        Handle events that affect the view.
        All events (e.g. focus in/out) reach the focus proxy, not this
        widget itself. That's why this event filter is necessary.
        """
        if self.focusProxy() is widget:
            if event.type() == QEvent.FocusIn:
                self.sig_focus_in_event.emit()
            elif event.type() == QEvent.FocusOut:
                self.sig_focus_out_event.emit()
        return super().eventFilter(widget, event)


class NotebookClient(QFrame):
    """
    Notebook client for Griffin.

    This is a widget composed of a NotebookWidget and a find dialog to
    render notebooks.

    Attributes
    ----------
    server_url : str or None
        URL to send requests to; set by register().
    """

    CONF_SECTION = CONF_SECTION

    def __init__(self, parent, filename, actions=None, ini_message=None):
        """
        Constructor.

        Parameters
        ----------
        parent : QWidget
            Parent of the widget under construction.
        filename : str
            File name of the notebook.
        actions : list of (QAction or QMenu or None) or None, optional
            Actions to be added to the context menu of the widget under
            construction. The default is None, meaning that no actions
            will be added.
        ini_message : str or None, optional
            HTML to be initially displayed in the widget. The default is
            None, meaning that an empty page is displayed initially.
        """
        super().__init__(parent)

        if os.name == 'nt':
            filename = filename.replace('/', '\\')
        self.filename = filename

        self.file_url = None
        self.server_url = None
        self.path = None

        self.notebookwidget = NotebookWidget(self, actions)
        if ini_message:
            self.notebookwidget.show_message(ini_message)
            self.static = True
        else:
            self.notebookwidget.show_blank()
            self.static = False

        self.notebookwidget.sig_focus_in_event.connect(
            lambda: self._apply_stylesheet(focus=True))
        self.notebookwidget.sig_focus_out_event.connect(
            lambda: self._apply_stylesheet(focus=False))
        self._apply_stylesheet()

        self.find_widget = FindReplace(self)
        self.find_widget.set_editor(self.notebookwidget)
        self.find_widget.hide()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.notebookwidget)
        layout.addWidget(self.find_widget)
        self.setLayout(layout)

    def add_token(self, url):
        """Add notebook token to a given url."""
        token_url = url + '?token={}'.format(self.token)
        return token_url

    def register(self, server_info):
        """Register attributes that can be computed with the server info."""
        # Path relative to the server directory
        self.path = os.path.relpath(self.filename,
                                    start=server_info['root_dir'])

        # Replace backslashes on Windows
        if os.name == 'nt':
            self.path = self.path.replace('\\', '/')

        # Server url to send requests to
        self.server_url = server_info['url']

        # Server token
        self.token = server_info['token']

        url = url_path_join(self.server_url, 'griffin-notebooks',
                            url_escape(self.path))

        # Set file url to load this notebook
        self.file_url = self.add_token(url)

    def go_to(self, url_or_text):
        """Go to page URL."""
        if isinstance(url_or_text, str):
            url = QUrl(url_or_text)
        else:
            url = url_or_text
        logger.debug(f'Going to URL {url_or_text}')
        self.notebookwidget.load(url)

    def load_notebook(self):
        """Load the associated notebook."""
        self.go_to(self.file_url)

    def get_filename(self):
        """Get notebook's filename."""
        return self.filename

    def get_short_name(self):
        """Get a short name for the notebook."""
        sname = osp.splitext(osp.basename(self.filename))[0]
        if len(sname) > 20:
            fm = QFontMetrics(QFont())
            sname = fm.elidedText(sname, Qt.ElideRight, 110)
        return sname

    def save(self):
        """
        Save current notebook asynchronously.

        This function simulates a click on the Save button in the notebook
        which will save the current notebook (but the function will return
        before). The Save button is found by selecting the first element of
        class `jp-ToolbarButtonComponent` whose `title` attribute begins with
        the string "Save".
        """
        self.notebookwidget.mousedown(
            '.jp-ToolbarButtonComponent[title^="Save"]')

    def get_session_url(self):
        """
        Get the kernel sessions URL of the client.

        Return a str with the URL or None, if no server is associated to
        the client.
        """
        if self.server_url:
            session_url = url_path_join(self.server_url, 'api/sessions')
            return self.add_token(session_url)
        else:
            return None

    def get_kernel_id(self):
        """
        Get the kernel id of the client.

        Return a str with the kernel id or None. On error, display a dialog
        box and return None.
        """
        sessions_url = self.get_session_url()
        if not sessions_url:
            return None

        try:
            sessions_response = requests.get(sessions_url)
        except requests.exceptions.RequestException as exception:
            msg = _('Griffin could not get a list of sessions '
                    'from the Jupyter Notebook server. '
                    'Message: {}').format(exception)
            QMessageBox.warning(self, _('Server error'), msg)
            return None

        if sessions_response.status_code != requests.codes.ok:
            msg = _('Griffin could not get a list of sessions '
                    'from the Jupyter Notebook server. '
                    'Status code: {}').format(sessions_response.status_code)
            QMessageBox.warning(self, _('Server error'), msg)
            return None

        if os.name == 'nt':
            path = self.path.replace('\\', '/')
        else:
            path = self.path

        sessions = json.loads(sessions_response.content.decode())
        for session in sessions:
            notebook_path = session.get('notebook', {}).get('path')
            if notebook_path is not None and notebook_path == path:
                kernel_id = session['kernel']['id']
                return kernel_id

    def shutdown_kernel(self):
        """Shutdown the kernel of the client."""
        kernel_id = self.get_kernel_id()

        if kernel_id:
            delete_url = self.add_token(url_path_join(self.server_url,
                                                      'api/kernels/',
                                                      kernel_id))
            delete_req = requests.delete(delete_url)
            if delete_req.status_code != 204:
                QMessageBox.warning(
                    self,
                    _("Server error"),
                    _("The Jupyter Notebook server "
                      "failed to shutdown the kernel "
                      "associated with this notebook. "
                      "If you want to shut it down, "
                      "you'll have to close Griffin."))

    def _apply_stylesheet(self, focus=False):
        """Apply stylesheet according to the current focus."""
        if focus:
            border_color = GriffinPalette.COLOR_ACCENT_3
        else:
            border_color = GriffinPalette.COLOR_BACKGROUND_4

        css = qstylizer.style.StyleSheet()
        css.QFrame.setValues(
            border=f'1px solid {border_color}',
            margin='0px 1px 0px 1px',
            padding='0px 0px 1px 0px',
            borderRadius='3px'
        )

        self.setStyleSheet(css.toString())


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
def main():
    """Execute a simple test."""
    from griffin.utils.qthelpers import qapplication
    app = qapplication()
    widget = NotebookClient(parent=None, filename='')
    widget.show()
    widget.go_to('http://google.com')
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
