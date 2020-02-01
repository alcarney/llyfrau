import pathlib
import unittest.mock as mock

import sphobjinv as soi

from llyfrau.data import Database, Source, Link
from llyfrau.importers import sphinx


def test_sphinx_import_complete_url(workdir):
    """Ensure that if the importer is called with a complete objects.inv url it is used
    as is.
    """

    filepath = str(pathlib.Path(workdir.name, "sphinx.db"))

    inv = soi.Inventory()
    inv.project = "Example"
    inv.version = "1.0"
    inv.objects.append(
        soi.DataObjStr(
            name="foo",
            domain="py",
            priority="1",
            role="function",
            uri="foo.html",
            dispname="-",
        )
    )

    with mock.patch("llyfrau.importers.soi.Inventory", return_value=inv) as m_inv:
        sphinx(filepath, "https://docs.python.org/3/objects.inv")

    m_inv.assert_called_with(url="https://docs.python.org/3/objects.inv")


def test_sphinx_import_folder_url(workdir):
    """Ensure that if the importer is called with a url ending with a '/' it tacks on
    a objects.inv'"""

    filepath = str(pathlib.Path(workdir.name, "sphinx.db"))

    inv = soi.Inventory()
    inv.project = "Example"
    inv.version = "1.0"
    inv.objects.append(
        soi.DataObjStr(
            name="bar",
            domain="py",
            priority="1",
            role="function",
            uri="bar.html",
            dispname="-",
        )
    )

    with mock.patch("llyfrau.importers.soi.Inventory", return_value=inv) as m_inv:
        sphinx(filepath, "https://docs.python.org/2/")

    m_inv.assert_called_with(url="https://docs.python.org/2/objects.inv")


def test_sphinx_import_word_url(workdir):
    """Ensure that if the importer is called with a url endining with a word it tacks on
    a '/objects.inv'"""

    filepath = str(pathlib.Path(workdir.name, "sphinx.db"))

    inv = soi.Inventory()
    inv.project = "Example"
    inv.version = "1.0"
    inv.objects.append(
        soi.DataObjStr(
            name="baz",
            domain="py",
            priority="1",
            role="function",
            uri="baz.html",
            dispname="-",
        )
    )

    with mock.patch("llyfrau.importers.soi.Inventory", return_value=inv) as m_inv:
        sphinx(filepath, "https://docs.python.org/1")

    m_inv.assert_called_with(url="https://docs.python.org/1/objects.inv")


def test_sphinx_import(workdir):
    """Ensure that the sphinx importer imports links correctly"""

    filepath = str(pathlib.Path(workdir.name, "sphinx-importer.db"))

    inv = soi.Inventory()
    inv.project = "Python"
    inv.version = "1.0"
    inv.objects.append(
        soi.DataObjStr(
            name="print",
            domain="py",
            priority="1",
            role="function",
            uri="builtins.html#$",
            dispname="-",
        )
    )
    inv.objects.append(
        soi.DataObjStr(
            name="enumerate",
            domain="py",
            priority="1",
            role="function",
            uri="builtins.html#$",
            dispname="function: Enumerate",
        )
    )

    with mock.patch("llyfrau.importers.soi.Inventory", return_value=inv) as m_inv:
        sphinx(filepath, "https://docs.python.org/")

    m_inv.assert_called_with(url="https://docs.python.org/objects.inv")

    db = Database(filepath)

    source = Source.get(db, 1)
    assert source.name == "Python - 1.0 | Sphinx Docs"
    assert source.prefix == "https://docs.python.org/"

    links = Link.search(db)

    assert links[0].name == "print"
    assert links[0].url == "builtins.html#print"
    assert links[0].source == source

    assert links[1].name == "function: Enumerate"
    assert links[1].url == "builtins.html#enumerate"
    assert links[1].source == source
