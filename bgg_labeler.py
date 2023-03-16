import os
from pathlib import Path
from svglib.svglib import svg2rlg
import svglib as svglib
from reportlab.graphics import renderPDF
import logging
import math
import svg_stack as ss
from tqdm import tqdm
from datetime import datetime
from boardgamegeek import BGGClient
import boardgamegeek as bggm
import xml.etree.ElementTree as xmlET
from PIL import ImageFont
from pypdf import PdfMerger

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('main')
LOGGER.setLevel(logging.DEBUG)
logging.getLogger("boardgamegeek.api").setLevel(logging.INFO)

USERNAME="ColbyBoardgames"
TEST_ID = 285967
SVG_TEMPLATE = "label_template.svg"
BUILDDIR = Path('build')
CACHEDIR = Path('cache')
RESDIR = Path('res')

COLOR_GREEN = '#008000'
COLOR_YELLOW = '#ca9a08'
COLOR_ORANGE = '#e27a07'
COLOR_RED = '#bb0707'

NOT_RECOMMENDED_TRESHOLD = 0.7

bgg = BGGClient(cache=bggm.CacheBackendSqlite(path=CACHEDIR / "cache.db", ttl=3600))

def game_info(game):
    """
    Returns a SimpleNamespace (dot-accessible "dict" object) with game information.
    """
    res = {}
    data = game.data()
    res['name'] = game.name
    res['id'] = game.id
    res['year'] = game.year
    weight = game.rating_average_weight
    res['weight'] = weight
    weight_label = ''
    weight_color = ''
    if weight <= 2:
        weight_label = 'Very Light'
        weight_color = COLOR_GREEN
    elif 2 < weight <= 2.8:
        weight_label = 'Light'
        weight_color = COLOR_GREEN
    elif 2.8 < weight <= 3.2:
        weight_label = 'Medium-Light'
        weight_color = COLOR_YELLOW
    elif 3.2 < weight <= 3.7:
        weight_label = 'Medium'
        weight_color = COLOR_ORANGE
    elif 3.7 < weight <= 4:
        weight_label = 'Medium-Heavy'
        weight_color = COLOR_ORANGE
    elif weight > 4:
        weight_label = 'Heavy'
        weight_color = COLOR_RED
    res['weight_label'] = f'{weight_label} ({game.rating_average_weight:.1f})'
    res['weight_color'] = weight_color
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
    rank_cutoffs = (1, 5, 10, 20, 50, 100, 200, 1000, math.inf)
    rank_class = min([r for r in rank_cutoffs if best_rank <= r])
    best_rank_name = best_rank_name.replace('games','').replace('boardgame','all time')
    if rank_class != math.inf:
        res['award'] = f"Top {rank_class} {best_rank_name}"
    res['rank'] = game.bgg_rank
    res['tags'] = game.categories

    not_recommended = []
    for ps in game.player_suggestions:
        d = ps.data()
        n = ps.numeric_player_count
        total = d['best'] + d['recommended'] + d['not_recommended']
        really_not_rec = NOT_RECOMMENDED_TRESHOLD < d['not_recommended'] / total
        within_count = game.min_players <= n <= game.max_players
        if really_not_rec and within_count:
            not_recommended.append(n)

    res['not_recommended'] = not_recommended
    if not_recommended:
        not_recommended.sort()
        not_recommended_ranges = [(not_recommended.pop(0),)]
        for n in not_recommended:
            last_range = not_recommended_ranges[-1]
            if n == 1 + last_range[-1]:
                not_recommended_ranges[-1] = (last_range[0], n)
            else:
                not_recommended_ranges.append((n,))
        not_recommended_str = ''
        for i, r in enumerate(not_recommended_ranges):
            if len(r) == 1:
                not_recommended_str += f'{r[0]}'
            else:
                not_recommended_str += f'{r[0]}-{r[1]}'
            if i < len(not_recommended_ranges) - 1:
                not_recommended_str += ','
        res['not_recommended_str'] = not_recommended_str

    return res

def set_content(tree, xpath, content, ns):
    element = tree.findall(xpath, ns)[-1]
    element.text = str(content)

def clear_content(tree, xpath, ns):
    element = tree.find(xpath, ns)
    element.clear()


ns = {'inkscape': "http://www.inkscape.org/namespaces/inkscape"}
label_xpath = "[@inkscape:label='%s']"
group_xpath = f".//*{label_xpath}"
span_xpath = f".//*{label_xpath}/*{label_xpath}//{{*}}tspan"
font = ImageFont.truetype("res/Roboto-Bold.ttf", 24)
MAX_LINELENGHT = 260 # px

def fill_truncate_text(tree, property, value):
    xpath = span_xpath % (f'{property}-group', f'{property}-text')
    max_length_string = tree.find(xpath, ns).text
    max_linelength = font.getlength(max_length_string)

    value = value.split(' ')

    while font.getlength(' '.join(value)) > max_linelength:
        value.pop()

    value = ' '.join(value)
    value.strip(' ,')
    set_content(tree, xpath, value, ns)
    

def fill_multi_line(tree, property, value):
    clear_content(
        tree, span_xpath % (f'{property}-group', f'{property}-text-short'), ns)
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
    set_content(tree, 
                span_xpath % (f'{property}-group', f'{property}-text-line1'), 
                line1,
                ns)
    set_content(tree, 
                span_xpath % (f'{property}-group', f'{property}-text-line2'), 
                line2,
                ns)

def fill_text(tree, property, value):
    multiline_supported = ['name']
    truncate_supported = ['tags']
    if property in multiline_supported:
        width = font.getlength(value)
        if width > MAX_LINELENGHT:
            fill_multi_line(tree, property, value)
        else:
            # delete line1 and line2
            clear_content(
                tree, span_xpath % (f'{property}-group', f'{property}-text-line1'), ns)
            clear_content(
                tree, span_xpath % (f'{property}-group', f'{property}-text-line2'), ns)
            set_content(tree, 
                        span_xpath % (f'{property}-group', f'{property}-text-short'), 
                        value,
                        ns)
    elif property in truncate_supported:
        fill_truncate_text(tree, property, value)
    elif property == 'rank':
        _, top_n, *category = value.split(' ')
        category = ' '.join(category)
        set_content(tree, 
                    span_xpath % (f'{property}-group', f'{property}-text-line1'), 
                    "Top " + top_n,
                    ns)
        set_content(tree, 
                    span_xpath % (f'{property}-group', f'{property}-text-line2'), 
                    category,
                    ns)
    else:
        set_content(tree, 
                    span_xpath % (f'{property}-group', f'{property}-text'), 
                    value,
                    ns)

def fill_template(game, svg_file=SVG_TEMPLATE):
    tree = xmlET.parse(svg_file)
    root = tree.getroot()
    attr_dict = {
        'name': 'name', 
        'weight': 'weight_label',
        'player-n': 'player_range',
        'weight_color': 'weight_color',
        'recommended-n': 'not_recommended_str',
        'time': 'time_range',
        'avgscore': 'rating',
        'rank': 'award',
        'tags': 'tags'
    }
    for svg_name, bg_attr in attr_dict.items():
        value = game.get(bg_attr)
        if type(value) == float:
            value = '%.1f' % value
        if type(value) == list or type(value) == tuple:
            value = ', '.join(value)
        if svg_name == 'recommended-n' and value:
            value += ')'
        if type(value) == str:
            value = value.replace(' - ', '–')
            value = value.replace('-', '–')
        try:
            if value is None:
                clear_content(root, group_xpath % f'{svg_name}-group', ns)
            elif svg_name == 'weight_color':
                weight_bg_rect = tree.find((group_xpath % 'weight-group') + '{*}rect', ns)
                weight_bg_rect.attrib['style'] = f'fill:{value};'
            else:
                fill_text(root, svg_name, value)
        except AttributeError as e:
            not_found = f"{svg_name}-group/{svg_name}-text"
            print(f"Could not find {not_found}. Is your SVG file correct?")
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

def join_pdf(files, output_file):
    merger = PdfMerger()
    for f in files:
        merger.append(f)
    merger.write(output_file)
    merger.close()

def export(files):
    out_files = []
    fontpath = RESDIR / 'Roboto-Black.ttf'
    svglib.fonts.register_font('Roboto', fontpath)
    svglib.fonts.register_font('Roboto', fontpath, 'Bold')
    for in_file in files:
        in_path = os.path.dirname(in_file) 
        in_basename = os.path.basename(os.path.splitext(in_file)[0]) 
        out_file = in_path + '/' + in_basename + '.pdf'
        drawing = svg2rlg(in_file)
        renderPDF.drawToFile(drawing, out_file)
        out_files.append(out_file)
    return out_files


def compose_all(files, rows, cols):
    page_files = []
    for i, n in enumerate(range(0,len(files),rows * cols)):
        out_file = BUILDDIR / f'pages/page{i}.svg'
        LOGGER.debug(f"Composing page {i}")
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

def write_svg(game, overwrite=False): 
    id = game.id
    out_path = BUILDDIR / f'games/{id}.svg'
    # LOGGER.info('Exporting ' + game.name)
    if overwrite or not os.path.isfile(out_path):
        thegame = game_info(game)
        tree = fill_template(thegame)
        tree.write(out_path)
    return out_path

    # tree.write('svg-out.svg')

def run(args):
    if not os.path.isdir(BUILDDIR):
        os.mkdir(BUILDDIR)
    if not os.path.isdir(BUILDDIR / 'games'):
        os.mkdir(BUILDDIR / 'games')
    if not os.path.isdir(BUILDDIR / 'pages'):
        os.mkdir(BUILDDIR / 'pages')

    if args.bgg_id:
        game_ids = [args.bgg_id]
    else:
        game_collection = get_game_collection(args.username)
        collection_games = game_collection.items
        if args.since:
            collection_games = [g for g in collection_games if datetime.fromisoformat(g.last_modified).date() > args.since]
        game_ids = [game.id for game in collection_games]

    print("Getting game information from BGG...")
    games = bgg.game_list(game_ids)
    svg_paths = []
    print("Exporting SVGs...")
    for game in tqdm(games):
        out_path = write_svg(game, args.cache)
        svg_paths.append(out_path)
    print("Composing SVGs...")
    svg_pages = compose_all(svg_paths, args.rows, args.columns)
    print("Exporting SVG pages to PDF...")
    out_pdfs = export(svg_pages)
    join_pdf(out_pdfs, args.out_file)
    print("All done!")
