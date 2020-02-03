import argparse
import collections
import inspect
import logging
import pathlib
import shutil
import sys

import appdirs
import pkg_resources

from llyfrau._version import __version__
from llyfrau.data import Database, Link, Source

from .tui import LinkTable

_LogConfig = collections.namedtuple("LogConfig", "level,fmt")
_LOG_LEVELS = [
    _LogConfig(level=logging.INFO, fmt="%(message)s"),
    _LogConfig(level=logging.DEBUG, fmt="[%(levelname)s]: %(message)s"),
    _LogConfig(level=logging.DEBUG, fmt="[%(levelname)s][%(name)s]: %(message)s"),
]


def _setup_logging(verbose: int, quiet: bool) -> None:
    """Setup the logging system according to the given args."""

    if quiet:
        return

    verbose = 0 if verbose < 0 else verbose

    try:
        conf = _LOG_LEVELS[verbose]
        others = False
    except IndexError:
        conf = _LOG_LEVELS[-1]
        others = True

    logger = logging.getLogger("llyfrau")
    logger.setLevel(conf.level)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(conf.fmt))
    logger.addHandler(console)

    if others:
        sql_logger = logging.getLogger("sqlalchemy")
        sql_logger.setLevel(logging.INFO)
        sql_logger.addHandler(console)


def add_link(filepath, url, name):
    db = Database(filepath, create=True)
    Link.add(db, name=name, url=url)


def find_sources(filepath):

    path = pathlib.Path(filepath)

    if not path.exists():
        print(f"Unable to find links database: {filepath}", file=sys.stderr)
        return -1

    ids = ["ID"]
    names = ["Name"]
    uris = ["URI"]
    prefixes = ["Prefix"]

    db = Database(filepath)

    for source in Source.search(db):
        ids.append(source.id)
        names.append(source.name)
        uris.append(source.uri)
        prefixes.append(source.prefix)

    print(format_table([ids, names, uris, prefixes]))


def open_link_ui(filepath):

    table_ui = LinkTable(filepath)
    table_ui.run()


def call_command(cmd, args):

    if args.filepath is None:
        base = appdirs.user_data_dir(appname="llyfr", appauthor=False)
        args.filepath = str(pathlib.Path(base, "links.db"))

    params = inspect.signature(cmd).parameters
    cmd_args = {name: getattr(args, name) for name in params}
    return cmd(**cmd_args)


def format_cell(text, width, placeholder=None):

    if placeholder is None:
        placeholder = "..."

    if len(text) <= width:
        return text.ljust(width)

    idx = width - len(placeholder)
    return text[:idx] + placeholder


def format_column(col):
    return ["" if c is None else str(c) for c in col]


def format_table(columns):

    term_width, _ = shutil.get_terminal_size()
    maxwidth = (term_width - len(columns) + 1) // len(columns)

    columns = [format_column(col) for col in columns]
    sizes = [max(len(c) for c in col) for col in columns]
    widths = [min(maxwidth, size) for size in sizes]

    fmt = " ".join(["{:<" + str(n) + "}" for n in widths])
    rows = []

    for i in range(len(columns[0])):
        row = [
            format_cell(col[i], width=widths[idx]) for idx, col in enumerate(columns)
        ]
        rows.append(fmt.format(*row))

    return "\n".join(rows)


def _load_importers(parent):
    """Load importers and attach them to the cli interface."""

    for imp in pkg_resources.iter_entry_points("llyfrau.importers"):
        cmd = parent.add_parser(imp.name, help=f"{imp.name} importer")
        cmd.add_argument("uri", help="where to import links from")

        impl = imp.load()
        cmd.set_defaults(run=impl)


cli = argparse.ArgumentParser()
cli.add_argument(
    "-f", "--filepath", type=str, help="filepath to the links database", default=None,
)
cli.add_argument(
    "-q", "--quiet", help="disable all console output", action="store_true"
)
cli.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="increase output verbosity, repeatable e.g. -v, -vv, -vvv, ...",
)
cli.add_argument("--version", action="store_true", help="show version and exit")

commands = cli.add_subparsers(title="commands")
add = commands.add_parser("add", help="add a link")
add.add_argument("url", help="the link to add")
add.add_argument("-n", "--name", help="name of the link")
add.set_defaults(run=add_link)

import_ = commands.add_parser("import", help="import links from a source")
importers = import_.add_subparsers(title="importers")
_load_importers(importers)

sources = commands.add_parser("sources", help="list all link sources")
sources.set_defaults(run=find_sources)

open_ = commands.add_parser("open", help="open a link")
open_.set_defaults(run=open_link_ui)


def main():

    args = cli.parse_args()

    if args.version:
        print(f"llyfr v{__version__}")
        return 0

    _setup_logging(args.verbose, args.quiet)

    if hasattr(args, "run"):
        return call_command(args.run, args)

    cli.print_help()
