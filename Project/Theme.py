import json
import os
import shutil
import sys


def _get_resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        absolute_path = os.path.join(sys._MEIPASS, relative)
    else:
        absolute_path = os.path.join(relative)
    return absolute_path


class Theme:
    @staticmethod
    def to_color(s: str):
        lst = s.split(',')
        return int(lst[0]), int(lst[1]), int(lst[2])

    def __init__(self, filePath="theme/default.json"):
        print("theme path:", filePath)
        if not os.path.exists(filePath):
            print(filePath, "could not be found, creating now...")
            if not os.path.exists("theme"):
                os.mkdir("theme")
            shutil.copyfile(_get_resource_path("theme/default.json"), "theme/default.json")
        JSON_OBJ = json.load(open(filePath, "r"))
        # musicListUi
        self.musicListUi_color_bg = Theme.to_color(JSON_OBJ["musicListUi"]["color"]["background"])
        self.musicListUi_color_number = Theme.to_color(JSON_OBJ["musicListUi"]["color"]["number"])
        self.musicListUi_color_title = Theme.to_color(JSON_OBJ["musicListUi"]["color"]["title"])
        self.musicListUi_color_subtitle = Theme.to_color(JSON_OBJ["musicListUi"]["color"]["subtitle"])
        # playUi
        self.playUi_color_bg = Theme.to_color(JSON_OBJ["playUi"]["color"]["background"])
        self.playUi_color_title = Theme.to_color(JSON_OBJ["playUi"]["color"]["title"])
        self.playUi_color_subtitle = Theme.to_color(JSON_OBJ["playUi"]["color"]["subtitle"])
        # playBar
        self.playUi_color_playBar_font_right = Theme.to_color(JSON_OBJ["playUi"]["color"]["playBar"]["font"]["right"])
        self.playUi_color_playBar_font_left = Theme.to_color(JSON_OBJ["playUi"]["color"]["playBar"]["font"]["left"])
        self.playUi_color_playBar_line = Theme.to_color(JSON_OBJ["playUi"]["color"]["playBar"]["line"])
        self.playUi_color_playBar_played = Theme.to_color(JSON_OBJ["playUi"]["color"]["playBar"]["played"])
        # lyric
        self.playUi_color_lyric_main_focus = Theme.to_color(JSON_OBJ["playUi"]["color"]["lyric"]["main"]["focus"])
        self.playUi_color_lyric_main_unfocused = Theme.to_color(
            JSON_OBJ["playUi"]["color"]["lyric"]["main"]["unfocused"])
        self.playUi_color_lyric_sub_focus = Theme.to_color(JSON_OBJ["playUi"]["color"]["lyric"]["sub"]["focus"])
        self.playUi_color_lyric_sub_unfocused = Theme.to_color(JSON_OBJ["playUi"]["color"]["lyric"]["sub"]["unfocused"])
        # volBar
        self.playUi_color_volBar_font = Theme.to_color(JSON_OBJ["playUi"]["color"]["volBar"]["font"])
        self.playUi_color_volBar_line = Theme.to_color(JSON_OBJ["playUi"]["color"]["volBar"]["line"])
        self.playUi_color_volBar_coverLine = Theme.to_color(JSON_OBJ["playUi"]["color"]["volBar"]["coverLine"])
