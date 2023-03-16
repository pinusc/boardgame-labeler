#!/usr/bin/env python
import sys
import argparse
from gui import main as start_gui
from bgg_labeler import run

class GuiAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        start_gui(parser.parse_args(' '))  # pass namespace with default arguments
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
                    prog='Boardgame Collection Labeler',
                    description='What the program does',
                    epilog='Text at the bottom of help')

    parser.add_argument('username', 
                        help="BGG username whose collection to get",
                        nargs='?')
    parser.add_argument('--gui', action=GuiAction, nargs=0)
    parser.add_argument('-c', '--columns', default=3)
    parser.add_argument('-r', '--rows', default=6)
    parser.add_argument('-o', '--out', default="labels.pdf", dest='out_file')
    parser.add_argument('--no-cache', dest="cache", action="store_false")
    parser.add_argument('--no-pdf', action="store_false",
                        help="Do not produce a final PDF, just SVG pages")
    parser.add_argument('--no-svg-pages', action="store_false",
                        help="Do not output a PDF or SVG pages, just labels")
    parser.add_argument('--since',
                        metavar='date',
                        type=lambda x: datetime.fromisoformat(x).date(),
                        help="Only consider boardgames added after this date")
    parser.add_argument('--bgg-id',
                        type=int,
                        help="Generate label only for this ID")
    args = parser.parse_args()
    if args.username:
        run(args)
    else:
        start_gui(args)

if __name__ == "__main__":
    main()
