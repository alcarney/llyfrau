import logging
import pathlib
import webbrowser

from typing import List

from sqlalchemy import Column, ForeignKey, Integer, Table, Text, create_engine, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

logger = logging.getLogger(__name__)
Base = declarative_base()


class Database:
    """Manages connections to the database."""

    def __init__(self, filepath, create=False, verbose=False):
        """Parameters

        :param filepath: The path to the database
        :param create: Optional. If :code:`True` the database will be created if it
                       doesn't already exist.
        :param verbose: Optional. If :code:`True` enable sqlaclhemy's logging of SQL
                        commands
        """
        logger.debug("Creating db instance for: %s", filepath)
        self.filepath = pathlib.Path(filepath)

        if create and not self.filepath.parent.exists():
            self.filepath.parent.mkdir(parents=True)

        self.engine = create_engine("sqlite:///" + filepath, echo=verbose)
        self.new_session = sessionmaker(bind=self.engine)
        self._session = None

        if create:
            Source.__table__.create(bind=self.engine, checkfirst=True)
            Link.__table__.create(bind=self.engine, checkfirst=True)
            Tag.__table__.create(bind=self.engine, checkfirst=True)
            tag_association_table.create(bind=self.engine, checkfirst=True)

    def commit(self):

        if self._session:
            self._session.commit()
            return

        raise RuntimeError("There is no session to commit!")

    def close(self):
        self.engine.dispose()

    @property
    def exists(self):
        """Determine if the database exists on disk."""
        return self.filepath.exists()

    @property
    def session(self):
        """Return the current session object."""

        if self._session is None:
            self._session = self.new_session()

        return self._session


class Source(Base):
    """Represents a source that a link was imported from."""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    """The id of the source."""

    name = Column(Text, nullable=False)
    """The name of the source."""

    prefix = Column(Text, nullable=True)
    """The prefix that should be added to each link, if given."""

    uri = Column(Text, nullable=False)
    """The uri that was used when importing the source."""

    links = relationship("Link", backref="source")
    """Any links that were imported with this source."""

    def __eq__(self, other):

        if not isinstance(other, Source):
            return False

        return all(
            [
                self.id == other.id,
                self.name == other.name,
                self.prefix == other.prefix,
                self.uri == other.uri,
            ]
        )

    def __repr__(self):
        return f"Source<{self.name}, {self.uri}>"

    @classmethod
    def add(cls, db, items=None, commit=True, **kwargs):
        """Add a link or collection of links to the given database."""

        session = db.session

        if items is None:
            dbitem = cls(**kwargs)
            session.add(dbitem)

        elif isinstance(items[0], dict):
            dbitems = [cls(**args) for args in items]
            session.add_all(dbitems)

        else:
            session.add_all(items)

        if commit:
            db.commit()

    @classmethod
    def get(cls, db, id):
        """Get a link with the given id from the database."""

        session = db.session
        item = session.query(cls).filter(cls.id == id).first()
        return item

    @classmethod
    def search(cls, db, name=None, top=10):
        """Search the given database for sources."""

        session = db.session
        filters = []

        if name is not None:
            filters.append(cls.name.ilike(f"%{name}%"))

        if len(filters) > 0:
            items = session.query(cls).filter(*filters)
        else:
            items = session.query(cls)

        db.commit()
        return items[:top]


tag_association_table = Table(
    "tag_associations",
    Base.metadata,
    Column("link_id", Integer, ForeignKey("links.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)


class Tag(Base):
    """Represents a tag."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    """The id of the tag."""

    name = Column(Text, nullable=False, unique=True)
    """The name of the tag."""

    links = relationship("Link", secondary=tag_association_table, back_populates="tags")
    """The links that have this tag."""

    def __hash__(self):
        return hash((self.name, self.id))

    def __eq__(self, other):

        if not isinstance(other, Tag):
            return False

        return all([self.id == other.id, self.name == other.name])

    def __repr__(self):
        return f"Tag<{self.name}, {len(self.links)} links>"

    @classmethod
    def add(cls, db, items=None, commit=True, **kwargs):
        """Add a link or collection of links to the given database."""

        session = db.session

        if items is None:
            dbitem = cls(**kwargs)
            session.add(dbitem)

        elif isinstance(items[0], dict):
            dbitems = [cls(**args) for args in items]
            session.add_all(dbitems)

        else:
            session.add_all(items)

        if commit:
            db.commit()

    @classmethod
    def search(cls, db: Database, name: str = None, top: int = 10):
        """Search the given database for links.

        :param db: The database object to search
        :param name: Only return links whose name contains the given string.
        :param top: Only return the top :code:`N` results. (Default :code:`10`)
        """

        session = db.session
        filters = []

        if name is not None:
            filters.append(cls.name.ilike(f"%{name}%"))

        query = session.query(cls)

        if len(filters) > 0:
            query = query.filter(*filters)

        return query[:top]

    @classmethod
    def get(cls, db, id=None, name=None):
        """Get a tag by name or id."""

        if id is None and name is None:
            raise ValueError("You must give a name or an id.")

        if id is not None:
            session = db.session
            item = session.query(cls).filter(cls.id == id).first()
            return item

        if name is not None:
            session = db.session
            item = session.query(cls).filter(cls.name == name).first()
            return item


class Link(Base):
    """Represents an individual link."""

    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    """The id of the link."""

    name = Column(Text, nullable=False)
    """The name of the link."""

    url = Column(Text, nullable=False)
    """The url of the link."""

    visits = Column(Integer, default=0)
    """The number of times a link has been visited."""

    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    """The id of the source the link was added with, if applicable"""

    tags = relationship("Tag", secondary=tag_association_table, back_populates="links")
    """The tags applied to this link."""

    def __eq__(self, other):

        if not isinstance(other, Link):
            return False

        return all(
            [
                self.id == other.id,
                self.url == other.url,
                self.source_id == other.source_id,
            ]
        )

    def __repr__(self):
        return f"{self.name} <{self.url_expanded}, {len(self.tags)} tags>"

    @property
    def url_expanded(self):
        """The full url, including the link's prefix if set."""

        if self.source and self.source.prefix:
            return f"{self.source.prefix}{self.url}"

        return self.url

    @classmethod
    def open(cls, db, link_id):
        """Open the link with the given id"""

        link = cls.get(db, link_id)
        url = link.url_expanded
        webbrowser.open(url)

        # Update the stats
        link.visits += 1
        db.commit()

    @classmethod
    def add(cls, db, items=None, commit=True, **kwargs):
        """Add a link or collection of links to the given database."""

        session = db.session

        if items is None:
            dbitem = cls(**kwargs)
            session.add(dbitem)

        elif isinstance(items[0], dict):
            dbitems = [cls(**args) for args in items]
            session.add_all(dbitems)

        else:
            session.add_all(items)

        if commit:
            db.commit()

    @classmethod
    def get(cls, db, id):
        """Get a link with the given id from the database."""

        session = db.session
        item = session.query(cls).filter(cls.id == id).first()
        return item

    @classmethod
    def search(
        cls,
        db: Database,
        name: str = None,
        source: Source = None,
        tags: List[str] = None,
        top: int = 10,
        sort: str = None,
    ):
        """Search the given database for links.

        The :code:`sort` parameter can be used to control the order in which the
        results are sorted by. The following options are valid:

        - :code:`None` (default), results are returned in the default sort order from
          the database
        - :code:`"visits"`, results are returned with the most visited links first.

        Invalid options will be ignored

        :param db: The database object to search
        :param name: Only return links whose name contains the given string.
        :param source: Only return links from the given source.
        :param tags: Only return links with the given tags
        :param top: Only return the top :code:`N` results. (Default :code:`10`)
        :param sort: The criteria to sort the results by. (Default :code:`None`)
        """

        session = db.session
        filters = []

        if name is not None:
            filters.append(cls.name.ilike(f"%{name}%"))

        if source is not None:
            filters.append(cls.source_id == source.id)

        if tags is not None:

            for tag in tags:
                filters.append(Link.tags.any(name=tag))

        query = session.query(cls)

        if len(filters) > 0:
            query = query.filter(*filters)

        if sort == "visits":
            query = query.order_by(desc(cls.visits))

        return query[:top]
