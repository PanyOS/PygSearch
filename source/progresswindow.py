import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

import os
import mimetypes
mimetypes.init()

COMPRESSED_EXTS = (".gz", ".tar", ".zip", ".7z")

def subdirs(path):
    try:
        if path == "/mnt":
            pass
        else:
            for entry in os.scandir(path):
                if entry.is_dir(follow_symlinks=False):
                    yield from subdirs(entry.path)
                else:
                    if entry.is_file():
                        yield Format.format_file_entry(entry)
                    elif entry.is_dir():
                        yield Format.format_dir_entry(entry)
    except PermissionError:
        pass

class Format:

    @staticmethod
    def format_time(seconds):
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(seconds))

    @staticmethod
    def format_size(bytes):
        if bytes < 100:
            return "{} Byte".format(bytes)
        elif bytes < 100000:
            return "{} KB".format(round(float(bytes) / 1000, 1))
        elif bytes < 100000000:
            return "{} MB".format(round(float(bytes) / 1000000, 1))
        else:
            return "{} GB".format(round(float(bytes) / 1000000000, 1))

    @staticmethod
    def format_file_entry(fileentry):
        file_type = "text-x-generic"
        guess_type = mimetypes.guess_type(fileentry.name)[0]
        
        if fileentry.name.endswith(COMPRESSED_EXTS): 
            file_type = "package-x-generic"
        elif guess_type:
            if "application" in guess_type:
                file_type = "application-x-executable"
            elif "audio" in guess_type:
                file_type = "audio-x-generic"
            elif "font" in guess_type:
                file_type = "font-x-generic"
            elif "image" in guess_type:
                file_type = "image-x-generic"
            elif "video" in guess_type:
                file_type = "video-x-generic"
            
        return file_type, fileentry.name, fileentry.path, os.path.splitext(fileentry.name)[1], \
                Format.format_size(fileentry.stat().st_size), Format.format_time(fileentry.stat().st_mtime)

    @staticmethod
    def format_dir_entry(direntry):
        return "folder", direntry.name, direntry.path, '', \
                Format.format_size(direntry.stat().st_size), Format.format_time(direntry.stat().st_mtime)

@Gtk.Template(filename="../ui/progresswindow.ui")
class ProgressWindow(Gtk.Window):
    __gtype_name__ = "ProgressWindow"

    progresslabel = Gtk.Template.Child()
    progressbar = Gtk.Template.Child()
    cancelbutton = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.break_loading = False
        self.finished = False
        self.label_text = "Loading project for {}"
        self.progressbar.set_pulse_step(.0001)
        self.cancelbutton.connect("clicked", self.on_cancel_clicked)
        self.show()

    def on_cancel_clicked(self, widget):
        self.break_loading = True

    def run(self, dir):
        self.progresslabel.set_text(self.label_text.format(dir[1]))
        self.progressbar.pulse()
        self.resize(400, 50)

class ThreadProgress:

    def show_progress(self):
        fs_message_dialog = Gtk.MessageDialog(transient_for=self, flags=0,
                                    message_type=Gtk.MessageType.WARNING,
                                    buttons=Gtk.ButtonsType.YES_NO, text="Loading filesystem warning")
        fs_message_dialog.format_secondary_text("Would you like to load current file system?")
        response_type = fs_message_dialog.run()
        fs_message_dialog.destroy()

        if response_type == Gtk.ResponseType.YES:
            progresswindow = ProgressWindow()
            progresswindow.show()

            def loading_dialog():
                import time
                time.sleep(1)
                progresswindow.destroy()

                load_message_dialog = Gtk.MessageDialog(transient_for=self, flags=0,
                                        message_type=Gtk.MessageType.INFO,
                                        buttons=Gtk.ButtonsType.OK, text="Loading status")
                if not progresswindow.break_loading:
                    load_message_dialog.format_secondary_text("Loading finished!")
                else:
                    load_message_dialog.format_secondary_text("Loading aborted!")
                load_message_dialog.run()
                load_message_dialog.destroy()

            def update_task():
                for path_info in subdirs("/"):
                    self.sort_switch = False
                    if progresswindow.break_loading:
                        self.add_filesystem_watches()
                        loading_dialog()
                        self.sort_switch = True
                        yield False
                    progresswindow.run(path_info)
                    self.data_list.append(path_info)
                    self.data_model.append(path_info)
                    self.apply_model()
                    yield True
                self.add_filesystem_watches()
                loading_dialog()
                self.sort_switch = True
                yield False

            def thread_task():
                idle_task = update_task()
                GLib.idle_add(idle_task.__next__)

            import threading
            thread = threading.Thread(target=thread_task)
            thread.daemon = True
            thread.start()