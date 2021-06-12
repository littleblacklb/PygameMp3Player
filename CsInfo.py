import time

DEFAULT_RECV_SIZE = 8

GET_MUSIC = b'00'
GET_MS_PLAYED = b'01'
IS_MUSIC_UPDATED = b'02'
IS_MUSIC_TIME_UPDATED = b'03'

CLIENT_CLOSE = b'10'
SERVER_CLOSE = b'11'

ANSWER_FALSE = b'20'
ANSWER_TRUE = b'21'


class MusicInfo:
    def __init__(self):
        self.ts = int(round(time.time() * 1000))
        self.music_data = None
        self.ms_played = -1
