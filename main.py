#!/usr/bin/env python
import requests
import os
import logging
import statistics
import math
import argparse
import svg_stack as ss
from glob import glob
from boardgamegeek import BGGClient
import boardgamegeek as bggm
from types import SimpleNamespace
import xml.etree.ElementTree as xmlET
import cairosvg
from PIL import ImageFont, ImageDraw, Image
from pypdf import PdfMerger

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('main')
LOGGER.setLevel(logging.DEBUG)
logging.getLogger("boardgamegeek.api").setLevel(logging.INFO)

USERNAME="ColbyBoardgames"
TEST_ID = 285967
SVG_TEMPLATE = "label_template.svg"
BUILDDIR = 'build'

bgg = BGGClient(cache=bggm.CacheBackendSqlite(path="cache/cache.db", ttl=-1))

def get_median_time(id):
    plays = bgg.plays(game_id=id)
    plays = [p for p in plays if p.duration > 0]
    n_plays = sum(p.quantity if p.quantity > 0 else 1 for p in plays)
    duration = sum(p.duration for p in plays)
    LOGGER.debug(f"playsession #: {len(plays)}")
    LOGGER.debug(f"play #: {n_plays}")
    play_times = [p.duration / (p.quantity if p.quantity else 1) for p in plays]
    return statistics.median(play_times)

def game_info(game, max_tag_len=30):
    """
    Returns a SimpleNamespace (dot-accessible "dict" object) with game information.
    """
    res = {}
    data = game.data()
    __import__('pdb').set_trace()
    res['name'] = game.name
    res['id'] = game.id
    res['year'] = game.year
    res['weight'] = game.rating_average_weight
    minplayers = data['minplayers']
    maxplayers = data['maxplayers']
    if minplayers == maxplayers:
        player_range = minplayers
    else:
        player_range = f"{minplayers} - {maxplayers}"
    res['player_range'] = player_range
    mintime = game.min_playing_time
    maxtime = game.max_playing_time
    if mintime == maxtime:
        time_range = f"{mintime} min"
    else:
        time_range = f"{mintime} - {maxtime} min"
    res['time_range'] = time_range


    res['playing_time_range'] = f"{game.min_playing_time} - {game.max_playing_time} min"
    res['rating'] = data['stats']['average']
    best_rank = math.inf
    best_rank_name = ""
    for rankinfo in game.ranks:
        if rankinfo.value is not None and rankinfo.value < best_rank:
            best_rank = rankinfo.value
            best_rank_name = rankinfo.name
        # if rankinfo['id'] == '1':
        #     rank = rankinfo['value']
        #     break
    rank_cutoffs = (1, 5, 10, 20, 50, 100, 200, 1000, math.inf)
    rank_class = min([r for r in rank_cutoffs if best_rank <= r])
    if rank_class != math.inf:
        res['award'] = f"Top {rank_class} {best_rank_name.replace('games','').replace('boardgame','all time')}"
    res['rank'] = game.bgg_rank
    res['tags'] = game.categories
    short_tags = ''
    for t in game.categories:
        if len(short_tags + ', ' + t) < max_tag_len:
            if short_tags == "":
                short_tags = t
            else:
                short_tags += ', ' + t
    res['short_tags'] = short_tags
    # res.median_time = get_median_time(game.id)
    return res

def set_content(tree, xpath, content, ns):
    element = tree.find(xpath, ns)
    element.text = str(content)

def clear_content(tree, xpath, ns):
    element = tree.find(xpath, ns)
    element.clear()

def fill_template(game, svg_file=SVG_TEMPLATE):
    ns = {'inkscape': "http://www.inkscape.org/namespaces/inkscape"}
    tree = xmlET.parse(svg_file)
    root = tree.getroot()
    label_xpath = "[@inkscape:label='%s']"
    group_xpath = f".//*{label_xpath}/"
    span_xpath = f".//*{label_xpath}/*{label_xpath}/{{*}}tspan"
    attr_dict = {
        'name': 'name', 
        'weight': 'weight',
        'player-n': 'player_range',
        'time': 'time_range',
        'avgscore': 'rating',
        'rank': 'award',
        'tags': 'short_tags'
    }
    font = ImageFont.truetype("res/Roboto-Bold.ttf", 24)
    MAX_LINELENGHT = 260 # px
    for svg_name, bg_attr in attr_dict.items():
        value = game.get(bg_attr)
        if type(value) == float:
            value = '%.1f' % value
        try:
            if value is None:
                clear_content(root, group_xpath % f'{svg_name}-group', ns)
            elif svg_name == 'name':
                width = font.getlength(value)
                if width > MAX_LINELENGHT:
                    clear_content(root, span_xpath % ('name-group', 'name-text-short'), ns)
                    line1 = value.split()
                    line2 = []
                    while font.getlength(' '.join(line1)) > MAX_LINELENGHT:
                        line2 = [line1.pop()] + line2
                    popped = False
                    while font.getlength(' '.join(line2) + '...') > MAX_LINELENGHT:
                        popped = True
                        line2.pop()
                    if popped:
                        line2.append('...')
                    line1 = ' '.join(line1)
                    line2 = ' '.join(line2)
                    set_content(root, 
                                span_xpath % (f'name-group', f'name-text-line1'), 
                                line1,
                                ns)
                    set_content(root, 
                                span_xpath % (f'name-group', f'name-text-line2'), 
                                line2,
                                ns)
                else:
                    clear_content(root, span_xpath % ('name-group', 'name-text-line1'), ns)
                    clear_content(root, span_xpath % ('name-group', 'name-text-line2'), ns)
                    set_content(root, 
                                span_xpath % (f'name-group', f'name-text-short'), 
                                value,
                                ns)
            else:
                set_content(root, 
                            span_xpath % (f'{svg_name}-group', f'{svg_name}-text'), 
                            value,
                            ns)
        except AttributeError as e:
            print(f"Could not find {svg_name}-group/{svg_name}-text. Is your SVG file correct?")
            raise e
    return tree
    
def compose_page(files, cols):
    doc = ss.Document()
    v_layout = ss.VBoxLayout()
    for n in range(0,len(files),cols):
        h_layout = ss.HBoxLayout()
        for f in files[n:n+cols]:
            h_layout.addSVG(f,alignment=ss.AlignTop|ss.AlignLeft)
        v_layout.addLayout(h_layout)
    doc.setLayout(v_layout)
    return doc

def join_pdf(files):
    merger = PdfMerger()
    for f in files:
        merger.append(f)
    merger.write("out.pdf")
    merger.close()

def export(files):
    out_files = []
    for in_file in files:
        out_file = os.path.dirname(in_file) + '/' + os.path.basename(os.path.splitext(in_file)[0]) + '.pdf'
        cairosvg.svg2pdf(file_obj=open(in_file, "rb"), write_to=out_file)
        out_files.append(out_file)
    return out_files


def compose_all(files, rows, cols):
    page_files = []
    print(files)
    print(len(files))
    for i, n in enumerate(range(0,len(files),rows * cols)):
        out_file = f'{BUILDDIR}/pages/page{i}.svg'
        print(f"Composing page {i}")
        page = compose_page(files[n:n + rows * cols], cols)
        page.save(out_file)
        page_files.append(out_file)
    return page_files

def get_game_collection(username):
    print(f"Getting game collection for {username}...")
    game_collection = bgg.collection(
        username,
        exclude_subtype='boardgameexpansion')
    return game_collection

def write_svg(game_collection): 
    game_ids = [game.id for game in game_collection.items]

    out_paths = []
    for id in game_ids:
        out_path = f'{BUILDDIR}/games/{id}.svg'
        if True or not os.path.isfile(out_path):
            g = bgg.game(game_id=id)
            thegame = game_info(g)
            print('Exporting ' + thegame['name'])
            tree = fill_template(thegame)
            tree.write(out_path)
            out_paths.append(out_path)
    return out_paths

    # tree.write('svg-out.svg')


def main():
    parser = argparse.ArgumentParser(
                    prog='Boardgame Collection Labeler',
                    description='What the program does',
                    epilog='Text at the bottom of help')

    parser.add_argument('username', 
                        help="BGG username whose collection to get")
    parser.add_argument('-c', '--columns', default=3)
    parser.add_argument('-r', '--rows', default=6)
    parser.add_argument('-o', '--out', default="labels.pdf")
    parser.add_argument('--no-pdf', action="store_false",
                        help="Do not produce a final PDF, just SVG pages")
    parser.add_argument('--no-svg-pages', action="store_false",
                        help="Do not produce a PDF or SVG pages, just individual labels")
    args = parser.parse_args()

    print(args.username)

    if not os.path.isdir(BUILDDIR):
        os.mkdir(BUILDDIR)
    if not os.path.isdir(f'{BUILDDIR}/games'):
        os.mkdir(f'{BUILDDIR}/games')
    if not os.path.isdir(f'{BUILDDIR}/pages'):
        os.mkdir(f'{BUILDDIR}/pages')

    game_collection = get_game_collection(args.username)
    svgs = write_svg(game_collection)
    svg_pages = compose_all(glob(f'{BUILDDIR}/games/*.svg'), 6, 3)
    out_pdfs = export(svg_pages)
    join_pdf(out_pdfs)

if __name__ == "__main__":
    main()
