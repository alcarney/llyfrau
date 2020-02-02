from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import has_focus
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Label, TextArea

from llyfrau.data import Database, Link

CURSOR = ">> "
SEPARATOR = " | "


class Column:
    def __init__(self, title: str):
        self.title = title
        self.col = FormattedTextControl(text=[], focusable=False)

    def width(self):

        text = self.col.text

        if isinstance(text, list) and len(text) == 0:
            lines = [""]

        if isinstance(text, list) and len(text) > 0:

            if isinstance(text[0], str):
                lines = text

            if isinstance(text[0], tuple):
                lines = [t[1] for t in text]

        if isinstance(text, str):
            lines = text.split("\n")

        maxlen = max([len(line) for line in lines])
        return max(maxlen, len(self.title))

    def clear(self):
        """Clear the column's contents"""
        self.col.text = []


class LinkTable:
    def __init__(self, filepath):
        self.db = Database(filepath)
        cursor = FormattedTextControl(
            focusable=True, text=[("", CURSOR)], show_cursor=False
        )
        sep = Window(width=len(SEPARATOR), char=SEPARATOR, style="class:line")

        self.ids = Column("ID")
        self.names = Column("Name")
        self.sources = Column("Source")
        self.urls = Column("URL")

        table_header = VSplit(
            [
                Label(text="", width=len(CURSOR)),
                sep,
                Label(self.ids.title, width=self.ids.width, style="bold"),
                sep,
                Label(self.names.title, width=self.names.width, style="bold"),
                sep,
                Label(self.sources.title, width=self.sources.width, style="bold"),
                sep,
                Label(self.urls.title, width=self.urls.width, style="bold"),
            ]
        )
        self.selection = Window(cursor, width=len(CURSOR), style="class:selector")
        table_body = VSplit(
            [
                self.selection,
                sep,
                Window(self.ids.col, width=self.ids.width),
                sep,
                Window(self.names.col, width=self.names.width),
                sep,
                Window(self.sources.col, width=self.sources.width),
                sep,
                Window(self.urls.col, width=self.urls.width),
            ]
        )

        self.prompt = TextArea(
            multiline=False,
            focusable=True,
            accept_handler=self._do_search,
            get_line_prefix=self._get_prompt,
        )

        table = HSplit([table_header, table_body])
        layout = HSplit([table, self.prompt])

        kb = KeyBindings()

        @kb.add("c-c", eager=True)
        @kb.add("q", filter=has_focus(self.selection))
        def close(event):
            event.app.exit()

        @kb.add("s", filter=has_focus(self.selection))
        def start_search(event):
            event.app.layout.focus(self.prompt)

        @kb.add("o", filter=has_focus(self.selection))
        @kb.add(Keys.Enter, filter=has_focus(self.selection))
        def open_link(event):
            cursor = self.selection.content.text
            idx = len(cursor)

            selected = self.ids.col.text[idx - 1]
            link_id = int(selected[1])

            Link.open(self.db, link_id)

        @kb.add(Keys.Down, filter=has_focus(self.selection))
        def next_item(event):
            cursor = self.selection.content.text
            idx = len(cursor)
            max_idx = len(self.ids.col.text)

            if idx + 1 > max_idx:
                return

            cursor.insert(0, ("", "\n"))

        @kb.add(Keys.Up, filter=has_focus(self.selection))
        def prev_item(event):
            cursor = self.selection.content.text
            idx = len(cursor)

            if idx == 1:
                return

            cursor.pop(0)

        self.app = Application(layout=Layout(layout), key_bindings=kb)

    def run(self):
        self._do_search()
        self.app.run()

    def _do_search(self, inpt: Buffer = None):
        self.selection.content.text = [("", CURSOR)]
        self.ids.clear()
        self.names.clear()
        self.sources.clear()
        self.urls.clear()

        name = None

        if inpt is not None and len(inpt.text) > 0:
            name = inpt.text

        links = Link.search(self.db, name=name, top=10)

        for idx, link in enumerate(links):

            newline = "\n" if idx < len(links) - 1 else ""

            self.ids.col.text.append(("", f"{link.id}{newline}"))
            self.names.col.text.append(("", f"{link.name}{newline}"))
            self.urls.col.text.append(("", f"{link.url_expanded}{newline}"))

            source = "" if not link.source else link.source.name
            self.sources.col.text.append(("", f"{source}{newline}"))

        self.app.layout.focus(self.selection)

    def _get_prompt(self, line_no, other):

        if has_focus(self.prompt)():
            return "Search: "

        return "[s]earch | [o]pen | [q]uit"
