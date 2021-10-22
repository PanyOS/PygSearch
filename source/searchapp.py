import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, Gdk

from searchwindow import SearchApplicationWindow
from accelerators import Accelerator
from conf import conf

APP_MAIN_OPTIONS = {"version": (ord("v"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Application version", None)}

APP_ACTION_DICT = {"new_window": ("app.new_window", ("<control>n",),),
                "quit_application": ("app.quit_application", ("<control>q",),),
                "open_preferences": ("app.open_preferences", ("<control>o",),),
                "about": ("app.about", ("<control>a",),)}

class SearchApplication(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, 
            application_id=conf.app_id, 
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs)

        self.new_window = False

        self.add_main_options()

    def do_startup(self):
        Gtk.Application.do_startup(self)

        APP_CALLBACK_DICT = {"new_window": self.new_window_callback,
                        "quit_application": self.quit_callback,
                        "open_preferences": self.open_preferences_callback,
                        "about": self.about_callback}
        Accelerator.register_actions(self, APP_ACTION_DICT, APP_CALLBACK_DICT)

    def do_activate(self):
        self.new_window_callback("new_window", None)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()

        if "version" in options:
            print(conf.app_version)

        self.activate()
        return 0

    def do_window_removed(self, widget):
        Gtk.Application.do_window_removed(self, widget)
        if not len(self.get_windows()):
            self.quit()

    def new_window_callback(self, action, parameter):
        window = SearchApplicationWindow(application=self)
        self.add_window(window)
        if not self.new_window:
            self.new_window = True
        window.present()

    def quit_callback(self, action, parameter):
        for window in self.get_windows():
            cancelled = window.emit(
                "delete-event", Gdk.Event.new(Gdk.EventType.DELETE))
            if cancelled:
                return
            window.destroy()
        self.quit()

    def open_preferences_callback(self, action, parameter):
        window = self.get_active_window()
        window.preferences_dialog.show()

    def about_callback(self, action, parameter):
        window = self.get_active_window()
        about_dialog = Gtk.AboutDialog(transient_for=window, 
                                        modal=True)
        about_dialog.set_logo_icon_name(conf.logo_icon_name)
        about_dialog.set_program_name(conf.app_name)
        about_dialog.set_version(conf.app_version)
        about_dialog.set_website_label(conf.app_website_label)
        about_dialog.set_website(conf.app_website)
        about_dialog.set_copyright(conf.app_copyright)
        about_dialog.set_license_type(conf.app_license)
        about_dialog.present()

    def add_main_options(self):
        for key, values in APP_MAIN_OPTIONS.items():
            self.add_main_option(key, values[0], values[1], values[2], 
                                        values[3], values[4])

if __name__ == "__main__":
    searchapp = SearchApplication()
    searchapp.run(sys.argv)