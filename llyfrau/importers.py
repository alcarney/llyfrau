import sphobjinv as soi

from .data import Database, Link, Source, Tag


class Collection:
    """A class used for bookeeping."""

    def __init__(self, db, imp_name):
        self.db = db
        self.imp_name = imp_name
        self.source = Source()
        self.links = []
        self.tag_cache = {}
        self.tags = {}

    @property
    def name(self):
        return self.source.name

    @name.setter
    def name(self, value):
        self.source.name = value

    @property
    def prefix(self):
        """The common prefix to every link in the collection"""
        return self.source.prefix

    @prefix.setter
    def prefix(self, value):
        self.source.prefix = value

    def _get_or_create_tag(self, name):
        """Try and find an existing tag with the name, else create it."""

        if name in self.tags:
            return self.tags[name]

        if name in self.tag_cache:
            return self.tag_cache[name]

        existing = Tag.get(self.db, name=name)

        if existing is not None:
            self.tag_cache[name] = existing
            return existing

        tag = Tag(name=name)
        self.tags[name] = tag
        return tag

    def add_link(self, name=None, url=None, tags=None):
        """Handles the detail of making links."""

        link = Link(name=name, url=url)

        if tags is None:
            tags = []

        tags.append(self.imp_name)

        for name in tags:
            tag = self._get_or_create_tag(name)
            link.tags.append(tag)

        self.links.append(link)


def define_importer(import_):
    """Function that handles the details of importing a list of links.

    The idea is that this function calls :code:`f` with the reference given on the
    command line to get the list of links to import. It then handles the details of
    updating the database with these links.
    """

    # This outer function needs to handle the args given on the command line.
    def link_importer(filepath, uri):

        db = Database(filepath, create=True)
        collection = Collection(db, import_.__name__)

        import_(uri, collection)

        source = collection.source
        source.uri = f"{import_.__name__}://{uri}"

        for l in collection.links:
            source.links.append(l)

        Source.add(db, items=[source], commit=False)
        Link.add(db, items=collection.links, commit=False)

        if len(collection.tags) > 0:
            Tag.add(db, items=list(collection.tags.values()), commit=False)

        db.commit()
        db.close()

    return link_importer


def importer(f=None):
    """Decorator for defining importers."""

    if f is None:
        return define_importer

    return define_importer(f)


@importer
def sphinx(uri: str, collection: Collection):
    """Import links from a sphinx documentation site."""

    if uri.endswith("/"):
        uri = f"{uri}objects.inv"

    if not uri.endswith("objects.inv"):
        uri = f"{uri}/objects.inv"

    print(f"Trying index url  : {uri}", end="\r")
    inv = soi.Inventory(url=uri)
    print(f"Found object index: {uri} with {inv.count} entries")

    collection.name = f"{inv.project} v{inv.version} Documentation"
    collection.prefix = uri.replace("objects.inv", "")

    for item in inv.objects:

        name = item.dispname_expanded
        url = item.uri_expanded
        tags = [t for t in [item.domain, item.role] if t is not None]

        collection.add_link(name=name, url=url, tags=tags)
