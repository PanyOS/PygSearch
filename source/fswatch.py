import pyinotify

class ThreadNotify:

    def add_notify(self):
        self.watch_manager = pyinotify.WatchManager()
        self.mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE

        class EventHandler(pyinotify.ProcessEvent):
            def process_IN_CREATE(self, event):
                print("Creating:", event.pathname)

            def process_IN_DELETE(self, event):
                print("Removing:", event.pathname)

        self.thread_notifier = pyinotify.ThreadedNotifier(self.watch_manager, EventHandler())
        self.thread_notifier.start()