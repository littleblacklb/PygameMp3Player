import re


def get_time_text(s):
    pattern = re.compile("\\[(\\d{2}:\\d{2})\\.\\d{2}\\](.*)")
    match = pattern.match(s)
    return match.group(1), match.group(2)


def convert_sec(time: str):
    m, s = time.split(':')
    m = int(m)
    s = int(s)
    return m * 60 + s


def get_lyric_dict(filePath):
    f = open(filePath, 'r', encoding='utf-8')
    lines = f.readlines()
    f.close()
    dt = {}
    for l in lines:
        time, text = get_time_text(l)
        s = convert_sec(time)
        dt[s] = text
    return dt


print(get_lyric_dict("lyric/kobasolo,春茶 - 夏恋慕.lrc"))
