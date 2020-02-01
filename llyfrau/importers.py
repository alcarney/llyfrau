from typing import List, Tuple

import sphobjinv as soi

from .data import Database, Link, Source


def define_importer(f):
    """Function that handles the details of importing a list of links.

    The idea is that this function calls :code:`f` with the reference given on the
    command line to get the list of links to import. It then handles the details of
    updating the database with these links.
    """

    # This outer function needs to handle the args given on the command line.
    def link_importer(filepath, uri):

        db = Database(filepath, create=True)

        source, links = f(uri)
        source.uri = f"{f.__name__}://{uri}"

        for l in links:
            source.links.append(l)

        Source.add(db, items=[source], commit=False)
        Link.add(db, items=links)

    return link_importer


def importer(f=None):
    """Decorator for defining importers."""

    if f is None:
        return define_importer

    return define_importer(f)


@importer
def sphinx(uri: str) -> Tuple[Source, List[Link]]:
    """Import links from a sphinx documentation site."""

    if uri.endswith("/"):
        uri = f"{uri}objects.inv"

    if not uri.endswith("objects.inv"):
        uri = f"{uri}/objects.inv"

    inv = soi.Inventory(url=uri)
    print(f"Found object index: {uri} with {inv.count} entries")

    prefix = uri.replace("objects.inv", "")
    source = Source(name=f"{inv.project} - {inv.version} | Sphinx Docs", prefix=prefix)

    links = []
    for item in inv.objects:
        name = item.dispname_expanded
        url = item.uri_expanded

        links.append(Link(name=name, url=url))

    return source, links
