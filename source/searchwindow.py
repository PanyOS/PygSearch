import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

import os

from treeview import TreeViewCommon, PATTERN_OPTIONS, OBJECT_OPTIONS
from fswatch import ThreadNotify
from progresswindow import ThreadProgress
from accelerators import Accelerator

NAME_DICT = {"All": None,
            "Audio": "audio-x-generic",
            "Compressed": "package-x-generic",
            "Document": "text-x-generic",
            "Executable": "application-x-executable",
            "Folder": "folder",
            "Picture": "image-x-generic",
            "Video": "video-x-generic"}

WIN_ACTION_DICT = {"update_filesystem": ("win.update_filesystem", ("<control>u",),),
                "close_window": ("win.close_window", ("<control>w",),),
                "show_filters": ("win.show_filters", ("<alt>f",),),
                "show_statusbar": ("win.show_statusbar", ("<alt>s",),),
                "copy": ("win.copy", ("<control>c",),),
                "open": ("win.open", ("<alt>o",),),
                "open_path": ("win.open_path", ("<alt>p",),)}

@Gtk.Template(filename="../ui/preferences.ui")
class PreferenceDialog(Gtk.Dialog):
    __gtype_name__ = "PreferenceDialog"

    preferences_ok_button = Gtk.Template.Child()

    simple_button = Gtk.Template.Child()
    case_button = Gtk.Template.Child()
    whole_word_button = Gtk.Template.Child()
    regex_button = Gtk.Template.Child()

    name_button = Gtk.Template.Child()
    path_button = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pattern_mode = PATTERN_OPTIONS[0]
        self.object_mode = OBJECT_OPTIONS[1]
        self.preferences_ok_button.connect("clicked", self.on_ok_clicked)

        self.simple_button.connect("toggled", self.on_word_button_toggled)
        self.case_button.connect("toggled", self.on_word_button_toggled)
        self.whole_word_button.connect("toggled", self.on_word_button_toggled)
        self.regex_button.connect("toggled", self.on_word_button_toggled)

        self.name_button.connect("toggled", self.on_object_button_toggled)
        self.path_button.connect("toggled", self.on_object_button_toggled)

        self.connect("delete-event", self.on_preferences_delete_event)

    def on_ok_clicked(self, widget):
        self.hide()

    def on_word_button_toggled(self, widget):
        self.pattern_mode = widget.get_property("label")

    def on_object_button_toggled(self, widget):
        self.object_mode = widget.get_property("label")

    def on_preferences_delete_event(self, widget, event):
        self.hide()
        return True

@Gtk.Template(filename="../ui/searchwindow.ui")
class SearchApplicationWindow(Gtk.ApplicationWindow, TreeViewCommon):
    __gtype_name__ = "SearchApplicationWindow"

    treeview = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    statusbar = Gtk.Template.Child()
    status_label = Gtk.Template.Child()
    text_combobox = Gtk.Template.Child()
    combobox_headbar = Gtk.Template.Child()
    show_filters_button = Gtk.Template.Child()
    show_statusbar_button = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_treeview()

        self.search_entry.connect("populate-popup", self.on_search_contextmenu_popup)
        self.search_entry.connect("search-changed", self.on_search_change)
        self.text_combobox.connect("changed", self.on_combobox_change)
        self.preferences_dialog = PreferenceDialog()
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.thread_notifier = None
        self.connect("delete-event", self.on_window_delete_event)

    def do_realize(self):
        Gtk.ApplicationWindow.do_realize(self)
        app = self.get_application()

        WIN_CALLBACK_DICT = {"update_filesystem": self.update_filesystem_callback,
                        "close_window": self.close_window_callback,
                        "show_filters": self.show_filters_callback,
                        "show_statusbar": self.show_statusbar_callback,
                        "copy": self.copy_callback,
                        "open": self.open_callback,
                        "open_path": self.open_path_callback}
        Accelerator.register_actions(app, WIN_ACTION_DICT, WIN_CALLBACK_DICT, win=self)

    def close_window_callback(self, action, parameter):
        self.destroy()

    def add_filesystem_watches(self):
        for data in self.data_list:
            if os.path.exists(data[2]):
                self.watch_manager.add_watch(data[2], self.mask)

    def update_filesystem_callback(self, action, parameter):
        ThreadNotify.add_notify(self)
        ThreadProgress.show_progress(self)

    def show_filters_callback(self, action, parameter):
        if self.show_filters_button.get_active():
            self.combobox_headbar.show()
        else:
            self.combobox_headbar.hide()

    def show_statusbar_callback(self, action, parameter):
        if self.show_statusbar_button.get_active():
            self.statusbar.show()
        else:
            self.statusbar.hide()

    def copy_callback(self, action, parameter):
        self.copy_treeview()

    def open_callback(self, action, parameter):
        self.open_treeview()

    def open_path_callback(self, action, parameter):
        self.open_path_treeview()

    def on_window_delete_event(self, widget, event):
        if self.thread_notifier:
            self.thread_notifier.stop()
        self.destroy()
        return True

    def on_search_contextmenu_popup(self, widget, menu):
        menu.remove(menu.get_children()[-1])
        menu.show_all()

    def on_search_change(self, widget):
        self.sort_switch = True
        self.keyword_filter = self.search_entry.get_text()
        self.filter_model.refilter()
        self.apply_model()

    def on_combobox_change(self, widget):
        self.class_filter = NAME_DICT[self.text_combobox.get_active_text()]
        self.filter_model.refilter()
        self.apply_model()