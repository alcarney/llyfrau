import pathlib

from sqlalchemy import create_engine, Column, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class DbOps:
    """Mixin class for database operations with ORM models."""

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
        db.commit()

        return item

    @classmethod
    def search(cls, db):
        """Search the given database for links."""

        session = db.session
        items = session.query(cls).all()
        db.commit()

        return items

    @classmethod
    def remove(cls, db, id):
        """Remove the given link id from the database."""


class Source(Base, DbOps):
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


class Link(Base, DbOps):
    """Represents an individual link."""

    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    """The id of the link."""

    name = Column(Text, nullable=False)
    """The name of the link."""

    url = Column(Text, nullable=False)
    """The url of the link."""

    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    """The id of the source the link was added with, if applicable"""

    def __eq__(self, other):

        if not isinstance(other, Link):
            return False

        return all(
            [self.id == other.id, self.name == other.name, self.url == other.url]
        )

    def __repr__(self):
        return f"{self.name} <{self.url}>"


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

        self.filepath = pathlib.Path(filepath)
        self.engine = create_engine("sqlite:///" + filepath, echo=verbose)
        self.new_session = sessionmaker(bind=self.engine)
        self._session = None

        if create:
            Source.__table__.create(bind=self.engine, checkfirst=True)
            Link.__table__.create(bind=self.engine, checkfirst=True)

    def commit(self):

        if self._session:
            self._session.commit()
            return

        raise RuntimeError("There is no session to commit!")

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
