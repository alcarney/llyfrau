import argparse
import inspect
import shutil
import sys
import webbrowser

from .data import Database, Link


def add_link(filepath, url, title):

    with Database(filepath) as db:
        link = Link(title=title, url=url)
        db.add(link)


def find_links(filepath):

    with Database(filepath) as db:
        links = db.query(Link.query(), Link)

        ids = ["ID"]
        titles = ["Title"]
        urls = ["URL"]

        for link in links:
            ids.append(link.id)
            titles.append(link.title)
            urls.append(link.url)

        print(format_table([ids, titles, urls]))


def open_link(filepath, id):

    with Database(filepath) as db:
        links = db.query(Link.get(id), Link)

        if len(links) == 0:
            print(f"Unable to find link with ID: {id}")
            return -1

        webbrowser.open(links[0].url)


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


cli = argparse.ArgumentParser()
cli.add_argument(
    "-f",
    "--filepath",
    type=str,
    help="filepath to the links database",
    default="links.db",
)

commands = cli.add_subparsers(title="commands")
add = commands.add_parser("add", help="add a new url")
add.add_argument("url", help="the url to add")
add.add_argument("-t", "--title", help="title of the url")
add.set_defaults(run=add_link)

search = commands.add_parser("search", help="find a link")
search.set_defaults(run=find_links)

open_ = commands.add_parser("open", help="open a link")
open_.add_argument("id", help="the id of the link")
open_.set_defaults(run=open_link)


def main():

    args = cli.parse_args()

    if hasattr(args, "run"):
        sys.exit(call_command(args.run, args))

    cli.print_help()


if __name__ == "__main__":
    main()
