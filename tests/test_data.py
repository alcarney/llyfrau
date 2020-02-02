import pytest
import unittest.mock as mock

from llyfrau.data import Database, Link, Source

from sqlalchemy.exc import IntegrityError


def test_source_add_single():
    """Ensure that we can add a single source to the database."""

    db = Database(":memory:", create=True, verbose=True)

    Source.add(
        db,
        name="Numpy",
        prefix="https://docs.scipy.org/doc/numpy/",
        uri="sphinx://https://docs/scipy.org/doc/numpy/",
    )

    source = Source.get(db, 1)
    expected = Source(
        id=1,
        name="Numpy",
        prefix="https://docs.scipy.org/doc/numpy/",
        uri="sphinx://https://docs/scipy.org/doc/numpy/",
    )

    assert source == expected


def test_source_add_many_dicts():
    """Ensure that we can add many sources to the database using a dictionary
    representation."""

    db = Database(":memory:", create=True, verbose=True)

    sources = [
        {
            "name": "Numpy",
            "prefix": "https://docs.scipy.org/doc/numpy/",
            "uri": "sphinx://https://docs/scipy.org/doc/numpy/",
        },
        {
            "name": "Python",
            "prefix": "https://docs.python.org/3/",
            "uri": "sphinx://https://docs.python.org/3/",
        },
    ]

    Source.add(db, items=sources)

    sources[0]["id"] = 1
    sources[1]["id"] = 2

    assert Source.search(db) == [Source(**args) for args in sources]


def test_source_add_many_instances():
    """Ensure that we can add many sources to the database using instances of the Source
    class."""

    db = Database(":memory:", create=True, verbose=True)

    sources = [
        Source(
            name="Numpy",
            prefix="https://docs.scipy.org/doc/numpy/",
            uri="sphinx://https://docs.scipy.org/doc/numpy/",
        ),
        Source(
            name="Python",
            prefix="https://docs.python.org/3/",
            uri="sphinx://https://docs.python.org/3/",
        ),
    ]

    Source.add(db, items=sources)

    sources[0].id = 1
    sources[1].id = 2

    assert Source.search(db) == sources


def test_source_requires_uri():
    """Ensure that a source requires a uri before it can be added to the database."""

    db = Database(":memory:", create=True, verbose=True)
    source = Source(name="Numpy")

    with pytest.raises(IntegrityError) as err:
        Source.add(db, items=[source])

    assert "sources.uri" in str(err.value)
    assert "NOT NULL" in str(err.value)


def test_source_requires_name():
    """Ensure that a source requires a name before it can be added to the database."""

    db = Database(":memory:", create=True, verbose=True)
    source = Source(uri="sphinx://https://docs.scipy.org/doc/numpy/")

    with pytest.raises(IntegrityError) as err:
        Source.add(db, items=[source])

    assert "sources.name" in str(err.value)
    assert "NOT NULL" in str(err.value)


def test_link_add_single():
    """Ensure that we can add a single link to the database."""

    db = Database(":memory:", create=True, verbose=True)

    Link.add(db, name="Github", url="https://www.github.com/")
    assert Link.get(db, 1) == Link(id=1, name="Github", url="https://www.github.com/")


def test_link_add_many_dicts():
    """Ensure that we can add many links to the database using a dictionary
    representation."""

    db = Database(":memory:", create=True, verbose=True)

    links = [
        {"name": "Github", "url": "https://www.github.com/"},
        {"name": "Google", "url": "https://google.com"},
        {"name": "Python", "url": "https://python.org"},
    ]

    Link.add(db, items=links)

    links[0]["id"] = 1
    links[1]["id"] = 2
    links[2]["id"] = 3

    assert Link.search(db) == [Link(**args) for args in links]


def test_link_add_many_instances():
    """Ensure that we can add many links to the database using instances of the link
    class."""

    db = Database(":memory:", create=True, verbose=True)

    links = [
        Link(name="Github", url="https://www.github.com"),
        Link(name="Google", url="https://www.google.com"),
        Link(name="Python", url="https://www.python.org"),
    ]

    Link.add(db, items=links)

    links[0].id = 1
    links[1].id = 2
    links[2].id = 3

    assert Link.search(db) == links


def test_link_requires_name():
    """Ensure that a link requires a name before it can be added to the database"""

    db = Database(":memory:", create=True, verbose=True)
    link = Link(url="https://www.google.com")

    with pytest.raises(IntegrityError) as err:
        Link.add(db, items=[link])

    assert "links.name" in str(err.value)
    assert "NOT NULL" in str(err.value)


def test_link_requires_url():
    """Ensure that a link requires a url before it can be added to the database"""

    db = Database(":memory:", create=True, verbose=True)
    link = Link(name="Google")

    with pytest.raises(IntegrityError) as err:
        Link.add(db, items=[link])

    assert "links.url" in str(err.value)
    assert "NOT NULL" in str(err.value)


def test_link_source_reference():
    """Ensure that a link can reference to source it was added by"""

    db = Database(":memory:", create=True, verbose=True)
    Source.add(
        db,
        name="Numpy",
        prefix="https://docs.scipy.org/doc/numpy/",
        uri="sphinx://https://docs.scipy.org/doc/numpy/",
    )

    Link.add(db, name="Reference Guide", url="reference/", source_id=1)

    link = Link.get(db, 1)
    assert link.source_id == 1

    source = Source.get(db, 1)
    assert source.links == [link]
    assert link.source == source


def test_open_link():
    """Ensure that we can open a link in the database"""

    db = Database(":memory:", create=True)
    Link.add(db, name="Github", url="https://www.github.com")

    with mock.patch("llyfrau.data.webbrowser") as m_webbrowser:
        Link.open(db, 1)

    m_webbrowser.open.assert_called_with("https://www.github.com")


def test_open_link_with_prefix():
    """Ensure that we can open a link that has a prefix on its source"""

    db = Database(":memory:", create=True)

    Source.add(
        db,
        name="Numpy",
        prefix="https://docs.scipy.org/doc/numpy/",
        uri="sphinx://https://docs.scipy.org/doc/numpy/",
    )
    Link.add(db, name="Reference Guide", url="reference/", source_id=1)

    with mock.patch("llyfrau.data.webbrowser") as m_webbrowser:
        Link.open(db, 1)

    m_webbrowser.open.assert_called_with("https://docs.scipy.org/doc/numpy/reference/")
