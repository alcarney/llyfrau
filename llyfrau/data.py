import pathlib
import sqlite3


class Link:

    TABLE = """\
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE
)
"""

    INSERT = """\
INSERT INTO links VALUES (?, ?, ?)
"""

    def __init__(self, id=None, title=None, url=None):
        self.id = id
        self.title = title
        self.url = url

    def __repr__(self):
        return f"{self.title}<{self.url}>"

    @classmethod
    def query(cls):
        return "SELECT * FROM links", tuple()

    @classmethod
    def get(cls, id):
        return "SELECT * FROM links WHERE id=?", (id,)

    @classmethod
    def from_row(cls, row):
        return cls(id=row[0], title=row[1], url=row[2])

    def as_row(self):
        return (self.id, self.title, self.url)


class Database:
    def __init__(self, filepath):
        self.filepath = pathlib.Path(filepath)
        self.connection = sqlite3.connect(self.filepath)

    def __enter__(self):
        return self

    def __exit__(self, etype, err, tback):
        self.connection.close()

    def init(self, item):

        c = self.connection.cursor()
        c.execute(item.TABLE)

        return c

    def add(self, item):
        """Add a new item to the db"""
        c = self.init(item)
        c.executemany(item.INSERT, [item.as_row()])
        self.connection.commit()

    def query(self, query, cls):
        """Run a query against the database."""

        query, params = query

        c = self.init(cls)
        c.execute(query, params)

        items = [cls.from_row(r) for r in c.fetchall()]
        return items
