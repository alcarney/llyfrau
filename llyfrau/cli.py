import argparse
import inspect
import pathlib
import shutil
import sys
import webbrowser

import pkg_resources

from .data import Database, Link, Source


def add_link(filepath, url, name):
    db = Database(filepath, create=True)
    Link.add(db, name=name, url=url)


def find_links(filepath):

    path = pathlib.Path(filepath)

    if not path.exists():
        print(f"Unable to find links database: {filepath}", file=sys.stderr)
        return -1

    ids = ["ID"]
    names = ["Name"]
    urls = ["URL"]

    db = Database(filepath)
    links = Link.search(db)

    for link in links:
        ids.append(link.id)
        names.append(link.name)
        urls.append(link.url)

    print(format_table([ids, names, urls]))


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


def open_link(filepath, id):

    db = Database(filepath)
    link = Link.get(db, id)

    url = link.url

    if link.source is not None and link.source.prefix is not None:
        url = f"{link.source.prefix}{url}"

    webbrowser.open(url)


def call_command(cmd, args):

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
    "-f",
    "--filepath",
    type=str,
    help="filepath to the links database",
    default="links.db",
)

commands = cli.add_subparsers(title="commands")
add = commands.add_parser("add", help="add a link")
add.add_argument("url", help="the link to add")
add.add_argument("-n", "--name", help="name of the link")
add.set_defaults(run=add_link)

import_ = commands.add_parser("import", help="import links from a source")
importers = import_.add_subparsers(title="importers")
_load_importers(importers)

search = commands.add_parser("search", help="find a link")
search.set_defaults(run=find_links)

sources = commands.add_parser("sources", help="list all link sources")
sources.set_defaults(run=find_sources)

open_ = commands.add_parser("open", help="open a link")
open_.add_argument("id", help="the id of the link")
open_.set_defaults(run=open_link)


def main():

    args = cli.parse_args()

    if hasattr(args, "run"):
        sys.exit(call_command(args.run, args))

    cli.print_help()
