import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class Configure:

    def __init__(self):
        self.app_name = "PygSearch"
        self.app_id = "org.freeinternet.searchapp"
        self.app_logo_icon_name = "system-search"
        self.app_version = "0.0.1"
        self.app_website = "https://github.com/cboxdoerfer/fsearch"
        self.app_copyright = "PanyOS"
        self.app_website_label = "PygSearch for everything search"
        self.app_license = Gtk.License.GPL_2_0

conf = Configure()