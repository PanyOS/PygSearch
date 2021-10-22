import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio

class Accelerator:

    def register_actions(app, action_dict, callback_dict, win=None):

        for action_name, (name, accel) in action_dict.items():
            app.set_accels_for_action(name, accel)
            action = Gio.SimpleAction.new(action_name, None)
            action.connect('activate', callback_dict[action_name])
            if win:
                win.add_action(action)
            else:
                app.add_action(action)