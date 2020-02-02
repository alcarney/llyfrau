import pathlib

from llyfrau.cli import add_link
from llyfrau.data import Database, Link


def test_add_link(workdir):
    """Ensure that we can add a link to the database"""

    filepath = pathlib.Path(workdir.name, "add.db")
    add_link(str(filepath), url="https://www.github.com", name="Github")

    db = Database(str(filepath), create=False)
    assert Link.get(db, 1) == Link(id=1, name="Github", url="https://www.github.com")
