import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

PATTERN_OPTIONS = ("Match Simple", "Match Case", "Match Whole Word", "Match Regex")
OBJECT_OPTIONS = ("Match Name", "Match Path")

COLUMN_NAMES = ("Icon", "Name", "Path", "Extension", "Size", "Date")
COLUMN_WIDTHS = (10, 50, 120, 30, 10, 50)

class TreeViewCommon:

    def set_treeview(self):
        self.set_treeview_model()
        self.set_treeview_columns()
        self.set_treeview_menu()

    def set_treeview_model(self):
        self.data_model = Gtk.ListStore(str, str, str, str, str, str)
        self.data_list = []
        self.filter_model = self.data_model.filter_new()
        self.filter_model.set_visible_func(self.filter_func)
        self.class_filter = None
        self.keyword_filter = None
        self.sort_switch = True
        self.sort_column_id = 0
        self.sort_order = Gtk.SortType.DESCENDING
        self.treeview.set_model(self.data_model)

    def set_treeview_columns(self):
        cellrenderertext = Gtk.CellRendererText()
        cellrenderertext.props.width = 30
        cellrenderertext.props.ellipsize = Pango.EllipsizeMode.END
        cellrenderertext.props.xalign = 0.
        cellrenderertext.props.weight = Pango.Weight.NORMAL
        cellrenderertext.props.strikethrough = False
        cellrenderertext.props.foreground = '#000000'
        cellrenderertext.props.background = '#FFFFFF'
        cellrenderertext.props.wrap_mode = Pango.WrapMode.WORD
        cellrendererpixbuf = Gtk.CellRendererPixbuf()

        for num, name in enumerate(COLUMN_NAMES):
            if num == 0:
                column = Gtk.TreeViewColumn(name, cellrendererpixbuf, icon_name=num)
            else:
                column = Gtk.TreeViewColumn(name, cellrenderertext, text=num)

            column.set_clickable(True)
            column.set_sort_indicator(True)
            column.connect("clicked", self.on_column_header_clicked)
            column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            column.set_min_width(COLUMN_WIDTHS[num])
            column.set_fixed_width(COLUMN_WIDTHS[num])
            column.set_expand(True)

            column.set_resizable(True)
            column.set_reorderable(True)
            self.treeview.append_column(column)
    
    def set_treeview_menu(self):
        self.treeview_menu = Gtk.Menu()
        copy_item = Gtk.MenuItem("Copy")
        copy_item.connect("activate", self.on_treeview_menuitem_clicked)
        open_item = Gtk.MenuItem("Open")
        open_item.connect("activate", self.on_treeview_menuitem_clicked)
        open_path_item = Gtk.MenuItem("Open Path")
        open_path_item.connect("activate", self.on_treeview_menuitem_clicked)

        self.treeview_menu.add(copy_item)
        self.treeview_menu.add(open_item)
        self.treeview_menu.add(open_path_item)

        self.treeview_menu.attach_to_widget(self.treeview, None)
        self.treeview.connect("button-press-event", self.on_treeview_menu_popup)

    def on_column_header_clicked(self, widget):
        widget.set_sort_order(self.sort_order)
        if widget.get_sort_order() == Gtk.SortType.ASCENDING:
            self.sort_order = Gtk.SortType.DESCENDING
        else:
            self.sort_order = Gtk.SortType.ASCENDING

        self.sort_column_id = COLUMN_NAMES.index(widget.get_title())
        self.apply_model()

    def on_treeview_menu_popup(self, widget, event):
        self.set_selected_info()

        if event.triggers_context_menu() and event.type == Gdk.EventType.BUTTON_PRESS:
            self.treeview.grab_focus()
            
            path = self.treeview.get_path_at_pos(int(event.x), int(event.y))
            if path is None:
                return False

            treeview_selection = self.treeview.get_selection()
            model, rows = treeview_selection.get_selected_rows()

            if path[0] not in rows:
                treeview_selection.unselect_all()
                treeview_selection.select_path(path[0])
                self.treeview.set_cursor(path[0])

            self.treeview_menu.show_all()
            self.treeview_menu.popup_at_pointer(event)
            return True
        return False

    def on_treeview_menuitem_clicked(self, widget):
        if widget.get_label() == "Copy":
            self.copy_treeview()
        elif widget.get_label() == "Open":
            self.open_treeview()
        elif widget.get_label() == "Open Path":
            self.open_path_treeview()

    def row_compare(self, model, row1, row2, user_data):
        sort_column, _ = model.get_sort_column_id()
        value1 = model.get_value(row1, sort_column)
        value2 = model.get_value(row2, sort_column)
        
        if value1 < value2:
            return -1
        elif value1 == value2:
            return 0
        else:
            return 1

    def filter_pass_number(self):
        filter_list = self.data_list
        if self.class_filter and self.class_filter != "All":
            class_filter_func = lambda item: True if item[0] == self.class_filter else False
            filter_list = list(filter(class_filter_func, filter_list))
        if self.keyword_filter:
            keyword_filter_func = lambda item: True if self.keyword_filter in item[2] else False
            filter_list = list(filter(keyword_filter_func, filter_list))
        return len(filter_list)
    
    def filter_func(self, model, iter, data=None):
        match = True
        pattern = self.keyword_filter
        sentence = None

        if self.class_filter and self.class_filter != "All":
            match = (self.class_filter == model[iter][0])
        if self.keyword_filter:
            sentence = model[iter][2]
            match_keyword = True

            if self.preferences_dialog.object_mode == OBJECT_OPTIONS[0]:
                sentence = model[iter][1]

            import re
            if self.preferences_dialog.pattern_mode == PATTERN_OPTIONS[0]:
                match_keyword = re.findall(pattern, sentence, re.IGNORECASE)
            elif self.preferences_dialog.pattern_mode == PATTERN_OPTIONS[1]:
                match_keyword = re.findall(pattern, sentence)
            elif self.preferences_dialog.pattern_mode == PATTERN_OPTIONS[2]:
                pattern = "\\b{}\\b".format(self.keyword_filter)
                match_keyword = re.findall(pattern, sentence, re.IGNORECASE)
            else:
                # regular expression & wildcard
                pass

            match = (match and bool(match_keyword))
        return match

    def apply_model(self):
        self.data_model.set_sort_column_id(self.sort_column_id, self.sort_order)
        if self.sort_switch:
            sort_model = Gtk.TreeModelSort(self.filter_model)
            sort_model.set_sort_func(self.sort_column_id, self.row_compare, None)
            self.treeview.set_model(sort_model)
        self.treeview.get_column(self.sort_column_id).set_sort_indicator(True)
        self.status_label.set_text("{} items".format(self.filter_pass_number()))

    def get_treeiter(self):
        return self.treeview.get_selection().get_selected()[1]
    
    def set_selected_info(self):
        model = self.treeview.get_model()
        treeiter = self.get_treeiter()

        if treeiter:
            self.status_label.set_text(model.get_value(treeiter, 2))

    def copy_treeview(self):
        model = self.treeview.get_model()
        treeiter = self.get_treeiter()

        if treeiter:
            value = model.get_value(treeiter, 2)
            self.clipboard.set_text(value, -1)

    def open_treeview(self):
        pass
    
    def open_path_treeview(self):
        pass