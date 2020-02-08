import pathlib

from llyfrau.cli import add_link
from llyfrau.data import Database, Link, Tag


def test_add_link(workdir):
    """Ensure that we can add a link to the database"""

    filepath = pathlib.Path(workdir.name, "links.db")
    add_link(str(filepath), url="https://www.github.com", name="Github", tags=None)

    db = Database(str(filepath), create=False)
    assert Link.get(db, 1) == Link(id=1, name="Github", url="https://www.github.com")


def test_add_link_with_new_tags(workdir):
    """Ensure that we can add a link with tags that don't exist in te database"""

    filepath = pathlib.Path(workdir.name, "links.db")
    add_link(
        str(filepath),
        url="https://www.google.com",
        name="Google",
        tags=["search", "google"],
    )

    db = Database(str(filepath), create=False)

    link = Link.search(db, name="Google")[0]
    assert link.url == "https://www.google.com"

    tags = {Tag.get(db, name="search"), Tag.get(db, name="google")}
    assert set(link.tags) == tags


def test_add_link_with_existing_tags(workdir):
    """Ensure that we can add a link with tags that already exist in the database"""

    filepath = pathlib.Path(workdir.name, "links.db")
    add_link(
        str(filepath),
        url="https://docs.python.org/3/argparse.html",
        name="Argparse",
        tags=["python", "docs"],
    )

    add_link(
        str(filepath),
        url="https://docs.python.org/3/optparse.html",
        name="Optparse",
        tags=["python", "docs"],
    )

    db = Database(str(filepath), create=False)

    link1 = Link.search(db, name="Argparse")[0]
    link2 = Link.search(db, name="Optparse")[0]
    assert set(link1.tags) == set(link2.tags)
