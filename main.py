#!/usr/bin/env python
import requests
import xml.etree.ElementTree as ET
import os

import logging as LOGGER
LOGGER.basicConfig(level=LOGGER.DEBUG)
# LOGGER = logging.getLogger('main')

USERNAME="ColbyBoardgames"
BASEURL="https://boardgamegeek.com/xmlapi2/"
CACHEFILE='cached-res.xml'

def get_game_info(id):
    r = requests.get(f"{BASEURL}thing?id={USERNAME}")
    if r:
        xmlstring = r.text
        print(xmlstring)
        tree = ET.fromstring(xmlstring)
        LOGGER.debug(tree.tag)
        LOGGER.debug(tree.attrib)
        for child in tree:
            LOGGER.debug(child.tag)
            LOGGER.debug(child.attrib)
            LOGGER.debug('============')
    

def get_games_ids(xmlstring):
    tree = ET.fromstring(xmlstring)
    root = tree
        # LOGGER.debug(f"{child.tag} : {child.attrib}")
    ids = [child.attrib.get('objectid') for child in root]
    return ids


def main():
    """Program entrypoint
    :returns: TODO

    """
    xmlstring = ''
    if os.path.exists(CACHEFILE):
        with open(CACHEFILE) as f:
            LOGGER.debug('Response cached:')
            xmlstring = f.read()
            # LOGGER.debug(xmlstring)
    
    if not xmlstring:
        # r = requests.get(BASEURL+"user?name=MeeplesAndMorselsClub")
        r = requests.get(f"{BASEURL}collection?username={USERNAME}")
        if r:
            LOGGER.debug(r)
            xmlstring = r.text
            with open(CACHEFILE, 'w') as f:
                LOGGER.debug('Caching response')
                LOGGER.debug(xmlstring)
                f.write(xmlstring)
    ids = get_games_ids(xmlstring)
    for id in ids[:1]:
        get_game_info(id)
    return ids

if __name__ == "__main__":
    main()
