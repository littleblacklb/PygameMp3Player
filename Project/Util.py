import json

import requests


def get_song_id(MUSIC_NAME, ARTIST_NAME=None, COVER=None) -> int:
    """
    Get song id on netease music with the music name
    :param MUSIC_NAME:  Music name
    :param ARTIST_NAME: Artist name (Optional)
    :param COVER:       Cover name  (Optional)
    :return: Return song id if has the music on netease music, otherwise return -1
    """
    rtn_obj = json.loads(
        requests.get("http://music.eleuu.com/search?keywords={} {}".format(MUSIC_NAME, ARTIST_NAME)).text)
    print(rtn_obj)
    # if rtn_obj["result"]["songCount"] == 0 or rtn_obj["code"] != 200:
    #     return -1
    try:
        songs = rtn_obj["result"]["songs"]
    except KeyError:
        return -1
    hasMore = rtn_obj["result"]["hasMore"]
    songTotal = rtn_obj["result"]["songCount"]
    for obj in songs:
        song_id = obj["id"]
        if COVER is not None and obj["album"]["name"].find(COVER) == -1:
            break
        if obj["name"].find(MUSIC_NAME) != -1:
            if ARTIST_NAME is None:
                return song_id
            for artist in obj["artists"]:
                for name in ARTIST_NAME:
                    if artist["name"].find(name) != -1:
                        return song_id
    return -1


def get_lyric_text(song_id: int) -> tuple[str, str]:
    """
    Get the lyric on the netease music
    :param song_id: Song id on netease music
    :return: tuple(lrc, tran_lrc)
    """
    rtn_obj = json.loads(requests.get("http://music.eleuu.com/lyric?id={}".format(song_id)).text)
    try:
        a = rtn_obj["lrc"]["lyric"]
    except KeyError:
        a = ""
    try:
        b = rtn_obj["tlyric"]["lyric"]
    except KeyError:
        b = ""
    return a, b
