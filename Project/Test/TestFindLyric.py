import json
import re

import requests

if __name__ == '__main__':
    MUSIC_NAME = "夏恋慕"
    data = re.split(r'[/-]', "kobasolo/春茶-夏恋慕")
    COVER = data.pop()
    ARTIST_NAME = data
    print(ARTIST_NAME, '-', COVER)
    rtn_obj = json.loads(
        requests.get("http://music.eleuu.com/search?keywords={} {}".format(MUSIC_NAME, ARTIST_NAME)).text)
    songs = rtn_obj["result"]["songs"]
    hasMore = rtn_obj["result"]["hasMore"]
    songTotal = rtn_obj["result"]["songCount"]
    f = False
    for obj in songs:
        song_id = obj["id"]
        if obj["album"]["name"].find(COVER) == -1:
            break
        if obj["name"].find(MUSIC_NAME) != -1:
            for artist in obj["artists"]:
                for name in ARTIST_NAME:
                    if artist["name"].find(name) != -1:
                        print("Found! id=", song_id, sep='')
                        f = True
                        break
                if f:
                    break
        if f:
            print(obj)
            f = False
