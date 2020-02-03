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


def test_link_add_default_visits():
    """Ensure that the visits field on a link is initialised to a sane value."""

    db = Database(":memory:", create=True, verbose=True)
    Link.add(db, name="Github", url="https://github.com/")

    link = Link.get(db, 1)
    assert link.visits == 0


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


def test_link_open():
    """Ensure that we can open a link in the database"""

    db = Database(":memory:", create=True, verbose=True)
    Link.add(db, name="Github", url="https://www.github.com")

    with mock.patch("llyfrau.data.webbrowser") as m_webbrowser:
        Link.open(db, 1)

    m_webbrowser.open.assert_called_with("https://www.github.com")


def test_link_open_with_prefix():
    """Ensure that we can open a link that has a prefix on its source"""

    db = Database(":memory:", create=True, verbose=True)

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


def test_link_open_updates_stats():
    """Ensure that when we visit a link, its stats are updated."""

    db = Database(":memory:", create=True, verbose=True)
    Link.add(db, name="Github", url="https://www.github.com", visits=1)

    with mock.patch("llyfrau.data.webbrowser") as m_webbrowser:
        Link.open(db, 1)

    m_webbrowser.open.assert_called_with("https://www.github.com")

    link = Link.get(db, 1)
    assert link.visits == 2


def test_link_search_basic():
    """Ensure that the simplest search just returns records in the db."""

    db = Database(":memory:", create=True, verbose=True)
    links = [Link(name=f"Link {i}", url=f"https://{i}") for i in range(20)]
    Link.add(db, items=links)

    results = Link.search(db)
    assert len(results) == 10


def test_link_search_top():
    """Ensure that the number of search results can be set."""

    db = Database(":memory:", create=True, verbose=True)
    links = [Link(name=f"Link {i}", url=f"https://{i}") for i in range(20)]
    Link.add(db, items=links)

    results = Link.search(db, top=15)
    assert len(results) == 15


def test_link_search_large_top():
    """Ensure that we can safely handle a page size larger than the number of
    results."""

    db = Database(":memory:", create=True, verbose=True)
    links = [Link(name=f"Link {i}", url=f"https://{i}") for i in range(20)]
    Link.add(db, items=links)

    results = Link.search(db, top=25)
    assert len(results) == 20


def test_link_search_by_name():
    """Ensure that we can filter search results by name and the search is case
    insensitive."""

    db = Database(":memory:", create=True, verbose=True)

    links = [
        Link(name="link 1", url="https://1"),
        Link(name="LiNk 2", url="https://2"),
        Link(name="BLINK3", url="https://3"),
        Link(name="item 4", url="https://4"),
        Link(name="9linkz", url="https://5")
    ]

    Link.add(db, items=links)
    results = Link.search(db, name='link')

    assert len(results) == 4
    assert all(['link' in l.name.lower() for l in results])


def test_link_search_by_name_returns_nothing():
    """Ensure that if the name matches nothing then nothing is returned."""

    db = Database(":memory:", create=True, verbose=True)

    links = [
        Link(name="link 1", url="https://1"),
        Link(name="LiNk 2", url="https://2"),
        Link(name="LINK3", url="https://3"),
        Link(name="item 4", url="https://4")
    ]

    Link.add(db, items=links)
    results = Link.search(db, name='kiln')

    assert len(results) == 0


def test_link_search_sort_by_visits():
    """Ensure that we can sort results by the number of times they have been visited."""

    db = Database(":memory:", create=True, verbose=True)

    links = [
        Link(name="link 1", url="https://1", visits=1),
        Link(name="LiNk 2", url="https://2", visits=0),
        Link(name="LINK3", url="https://3", visits=1),
        Link(name="item 4", url="https://4", visits=2)
    ]

    Link.add(db, items=links)
    results = Link.search(db, sort='visits')

    assert results[0].url == "https://4"
    assert results[1].url == "https://1"
    assert results[2].url == "https://3"
    assert results[3].url == "https://2"

