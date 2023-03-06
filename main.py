#!/usr/bin/env python
import requests
import xml.etree.ElementTree as ET
import os
import logging
import statistics
from boardgamegeek import BGGClient
import boardgamegeek as bggm
from types import SimpleNamespace

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('main')
LOGGER.setLevel(logging.DEBUG)
logging.getLogger("boardgamegeek.api").setLevel(logging.INFO)

USERNAME="ColbyBoardgames"
TEST_ID = 285967

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


def game_info(game):
    """
    Returns a SimpleNamespace (dot-accessible "dict" object) with game information.
    """
    res = SimpleNamespace()
    data = game.data()
    res.name = game.name
    res.id = game.id
    res.year = game.year
    res.weight = game.rating_average_weight
    minplayers = data['minplayers']
    maxplayers = data['maxplayers']
    if minplayers == maxplayers:
        player_range = minplayers
    else:
        player_range = f"{minplayers} - {maxplayers}"
    res.player_range = player_range
    res.rating = data['stats']['average']
    rank = -1
    for rankinfo in data['stats']['ranks']:
        if rankinfo['id'] == '1':
            rank = rankinfo['value']
            break
    res.rank = rank
    # res.median_time = get_median_time(game.id)
    return res


def main():
    """Program entrypoint
    :returns: TODO
    """
    print(f"Getting game collection for {USERNAME}...")
    game_collection = bgg.collection(
        USERNAME,
        exclude_subtype='boardgameexpansion')
        # exclude_subtype=[bggm.utils.BGGRestrictCollectionTo.BOARD_GAME_EXTENSION])
    game_ids = [game.id for game in game_collection.items]
    games = bgg.game_list(game_id_list=game_ids)
    print(f"Got a list of {len(games)}!")
    for game in games:
        __import__('pprint').pprint(game_info(game))
    __import__('pprint').pprint(games[1].data())


if __name__ == "__main__":
    main()
