#!/usr/bin/env python
import requests
import xml.etree.ElementTree as ET
import os
import logging as LOGGER
from boardgamegeek import BGGClient
import boardgamegeek as bggm

LOGGER.basicConfig(level=LOGGER.WARNING)
# LOGGER = logging.getLogger('main')

USERNAME="ColbyBoardgames"

bgg = BGGClient()


def main():
    """Program entrypoint
    :returns: TODO
    """
    game_collection = bgg.collection(
        USERNAME,
        exclude_subtype='boardgameexpansion')
        # exclude_subtype=[bggm.utils.BGGRestrictCollectionTo.BOARD_GAME_EXTENSION])
    game_ids = [game.id for game in game_collection.items]
    games = bgg.game_list(game_id_list=game_ids)
    for game in games:
        print('')
        print("====== " + game.name + " " + "="*(80-len(game.name)))
        print(f"Weight: {game.rating_average_weight}")
        data = game.data()
        minplayers = data['minplayers']
        maxplayers = data['maxplayers']
        if minplayers == maxplayers:
            player_range = minplayers
        else:
            player_range = f"{minplayers} - {maxplayers}"
        rating = data['stats']['average']
        rank = -1
        for rankinfo in data['stats']['ranks']:
            if rankinfo['id'] == '1':
                rank = rankinfo['value']
                break
        print(f"Rank: {rank}")
        print(f"User Rating: {rating}")
        print(f"Players: {player_range}")


if __name__ == "__main__":
    main()
