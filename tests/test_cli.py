import pathlib
from unittest.mock import patch

from llyfrau.cli import add_link, open_link
from llyfrau.data import Database, Link, Source


def test_add_link(workdir):
    """Ensure that we can add a link to the database"""

    filepath = pathlib.Path(workdir.name, "add.db")
    add_link(str(filepath), url="https://www.github.com", name="Github")

    db = Database(str(filepath), create=False)
    assert Link.get(db, 1) == Link(id=1, name="Github", url="https://www.github.com")


def test_open_link(workdir):
    """Ensure that we can open a link in the database"""

    filepath = pathlib.Path(workdir.name, "open.db")
    db = Database(str(filepath), create=True)
    Link.add(db, name="Github", url="https://www.github.com")

    with patch("llyfrau.cli.webbrowser") as m_webbrowser:
        open_link(str(filepath), 1)

    m_webbrowser.open.assert_called_with("https://www.github.com")


def test_open_link_with_prefix(workdir):
    """Ensure that we can open a link that has a prefix on its source"""

    filepath = pathlib.Path(workdir.name, "open-prefix.db")
    db = Database(str(filepath), create=True)

    Source.add(
        db,
        name="Numpy",
        prefix="https://docs.scipy.org/doc/numpy/",
        uri="sphinx://https://docs.scipy.org/doc/numpy/",
    )
    Link.add(db, name="Reference Guide", url="reference/", source_id=1)

    with patch("llyfrau.cli.webbrowser") as m_webbrowser:
        open_link(str(filepath), 1)

    m_webbrowser.open.assert_called_with("https://docs.scipy.org/doc/numpy/reference/")
