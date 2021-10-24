# coding=utf-8

import configparser
import hashlib
import math
import os
import random
import re
import string
import sys
import time
import traceback
from enum import Enum

import eyed3
import pygame

from Pinyin2Hanzi import DefaultDagParams, dag
from Theme import Theme

SCREEN_W, SCREEN_H = 1024, 768


class PygameMp3Player(object):
    def __init__(self, temp_path: str, music_path: str, lyric_path: str, isEmpty: bool, skinFile: str = None):
        """
        FrameWork初始化
        :param music_path: 音乐目录
        """
        """
        pygame初始化        
        """
        if hasattr(sys, "_MEIPASS"):
            print(sys._MEIPASS)
            print(os.listdir(sys._MEIPASS))  # 打印资源目录
        pygame.init()
        self.scr: pygame.SurfaceType = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        # pygame.display.set_icon(pygame.image.load("D:\Python\PygameMp3Player\logo.png"))
        pygame.display.set_caption("Pygame Mp3 Player V1.2")
        """
        字体初始化
        """
        font_path = get_resource_path("font/msyhl.ttc")
        self.font12 = pygame.font.Font(font_path, 12)
        self.font16 = pygame.font.Font(font_path, 16)
        self.font18 = pygame.font.Font(font_path, 18)
        self.font20 = pygame.font.Font(font_path, 20)
        self.font25 = pygame.font.Font(font_path, 25)
        self.font32 = pygame.font.Font(font_path, 32)
        """
        var初始化
        """
        if skinFile is None:
            self.theme = Theme()
        else:
            self.theme = Theme(skinFile)
        self.manager = PlayManager(self)
        self.manager.isEmpty = isEmpty
        self.tempPath = temp_path
        self.status = UiEnum.musicListUi
        """
        简单的枚举当前文件夹寻找mp3文件(当然不支持递归深入查找)
        """
        pattern = re.compile("^.*.mp3$")
        t0 = time.time()
        for name in os.listdir(music_path):
            if pattern.match(name) is not None:  # 匹配是否为mp3
                lrcFile, lrcTranFile = None, None
                lrcName = name.split('.')[0]
                if os.path.exists(lyric_path + "/" + lrcName + ".lrc"):
                    lrcFile = lyric_path + "/" + lrcName + ".lrc"
                    if os.path.exists(lyric_path + "/" + lrcName + "_tran.lrc"):
                        lrcTranFile = lyric_path + "/" + lrcName + "_tran.lrc"
                musicObj = Music(self, music_path + "/" + name, lrcFile, lrcTranFile)
                self.manager.musicLst.append(musicObj)
                print("load: ", musicObj)
        print("用时", (time.time() - t0) * 1000, "ms")
        """
        UI初始化
        """
        playUI = PlayUI(self)
        self.uiLst = [MusicListUI(self, playUI), playUI]

    def show(self):
        self.scr.fill((0, 0, 0))
        self.uiLst[self.status.value].show(self.scr)
        pygame.display.update()

    def mouse_down(self, pos, btn):
        self.uiLst[self.status.value].mouse_down(pos, btn)

    def mouse_up(self, pos, btn):
        self.uiLst[self.status.value].mouse_up(pos, btn)

    def mouse_motion(self, pos):
        self.uiLst[self.status.value].mouse_motion(pos)

    def key_up(self, key):
        self.uiLst[self.status.value].key_up(key)

    def key_down(self, key):
        self.uiLst[self.status.value].key_down(key)


# CONTROL
class Button(object):
    def __init__(self, fWork: PygameMp3Player, picFile, x, y, btn_func, colorKey=(0, 0, 0), scale=None):
        if scale is not None:
            self.img: pygame.SurfaceType = pygame.transform.scale(pygame.image.load(picFile), scale)
        else:
            self.img: pygame.SurfaceType = pygame.image.load(picFile)
        self.fw = fWork
        self.img.set_colorkey(colorKey)
        self.w, self.h = self.img.get_width(), self.img.get_height()
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.status = 0
        self.btn_func = btn_func

    def show(self, scr: pygame.SurfaceType):
        scr.blit(self.img, (self.x, self.y), (self.status * self.rect.w, 0, self.rect.w, self.rect.h))

    def mouse_down(self, pos):
        if self.rect.collidepoint(pos):
            self.status = 1

    def mouse_up(self, pos):
        if not self.rect.collidepoint(pos) or self.status != 1:  # 必须当前按钮被按下后才有必要去执行
            self.status = 0
            return
        self.status = 0
        self.btn_func()


class PlayBar(object):
    def __init__(self, fWork: PygameMp3Player):
        self.fw = fWork
        self.status = 0
        self.x0, self.x1, = 125, 900
        self.w = self.x1 - self.x0
        self.playedW = 0
        self.y = SCREEN_H - 180
        self.rect = pygame.Rect(self.x0, self.y - 16, self.x1 - self.x0, 32)
        self.sec_all = 0
        self.clr_font_left = self.fw.theme.playUi_color_playBar_font_left
        self.clr_font_right = self.fw.theme.playUi_color_playBar_font_right
        self.clr_line = self.fw.theme.playUi_color_playBar_line
        self.clr_played = self.fw.theme.playUi_color_playBar_played

    def show(self, scr: pygame.SurfaceType):
        # pygame.draw.rect(scr, (102, 204, 255), self.rect)  # 这个不用我解释了吧...
        pygame.draw.line(scr, self.clr_line, (self.x0, self.y), (self.x1, self.y), 3)
        self.display_played_logic(scr)
        textSurface = self.fw.font18.render(convert_to_minute(self.fw.manager.timeManager.ms_played // 1000),
                                            True, self.clr_font_left)
        scr.blit(textSurface, (self.x0 - 65, self.y - 16))
        textSurface = self.fw.font18.render(convert_to_minute(self.sec_all), True, self.clr_font_right)
        scr.blit(textSurface, (self.x1 + 25, self.y - 16))

    def display_played_logic(self, scr):
        if self.fw.manager.isPlay or self.status:  # 更新ms_hasPlayed进度, status是用来更新已经拖动进度后的
            if self.fw.manager.currMusic.src is not None:  # 判断是否未播放过任何音乐 (fixed: 未播放时拖动进度条ms_hasPlayed显示异常时间
                self.fw.manager.timeManager.update()
        if self.fw.manager.currMusic.src is not None:  # 防止被除数为0
            sec_played = self.fw.manager.timeManager.ms_played / 1000
            self.playedW = self.w // (self.sec_all / sec_played)
            pygame.draw.line(scr, self.clr_played, (self.x0, self.y), (self.x0 + self.playedW, self.y), 3)

    def mouse_down(self, pos, btn):
        if self.rect.collidepoint(pos):
            self.status = 1

    def mouse_up(self, pos, btn):
        if self.status and self.playedW > 0:
            if self.fw.manager.currMusic.src is not None:  # 防止 set_pos unsupported for this codec
                self._do_time_change(pos)
                self.fw.manager.timeManager.update_location_mp3(self.sec_all / (self.w / self.playedW))
            self.status = 0

    def mouse_motion(self, pos):
        if self.status == 1:
            self._do_time_change(pos)

    def _get_played_weight(self, pos):
        if pos[0] <= self.x0:
            x = self.x0 + 1
        elif pos[0] >= self.x1:
            x = self.x1 - 1
        else:
            x = pos[0]
        return x - self.x0

    def _do_time_change(self, pos):
        self.playedW = self._get_played_weight(pos)
        sec = self.sec_all / (self.w / self.playedW)  # 新的播放进度
        self.fw.manager.timeManager.change(sec)


class VolumeBar(object):
    def __init__(self, fWork: PygameMp3Player):
        self.fw = fWork
        self.status = 0
        self.x0, self.x1, = SCREEN_W - 215, SCREEN_W - 115
        self.w = self.x1 - self.x0
        self.y = SCREEN_H - 100
        self.currW = 100
        self.vol = 100
        self.rect = pygame.Rect(self.x0, self.y - 16, self.x1 - self.x0, 32)
        self.clr_font = self.fw.theme.playUi_color_volBar_font
        self.clr_line = self.fw.theme.playUi_color_volBar_line
        self.clr_currVol = self.fw.theme.playUi_color_volBar_coverLine

    def show(self, scr: pygame.SurfaceType):
        # pygame.draw.rect(scr, (102, 204, 255), self.rect) # 这个不用我解释了吧...
        pygame.draw.line(scr, self.clr_line, (self.x0, self.y), (self.x1, self.y), 3)
        if self.currW != 0:  # 如果音量为0 就不画
            pygame.draw.line(scr, self.clr_currVol, (self.x0, self.y), (self.x0 + self.currW, self.y), 3)
        img = self.fw.font12.render(str(self.vol) + '%', True, self.clr_font)
        scr.blit(img, (self.x0 - 12, self.y - 16))

    def mouse_down(self, pos, btn):
        if self.rect.collidepoint(pos):
            self.status = 1

    def mouse_up(self, pos, btn):
        if self.status:
            self._change_new_volume(pos)
            print("vol. change to", self.vol)
        self.status = 0

    def mouse_motion(self, pos):
        if self.status == 1:
            self._change_new_volume(pos)

    def _change_new_volume(self, pos):
        n = 0
        if pos[0] <= self.x0:
            x = self.x0 + 1
            n = 1
        elif pos[0] >= self.x1:
            x = self.x1
        else:
            x = pos[0]
        divCurrW = x - self.x0  # 被除数不能为0
        self.currW = divCurrW - n
        self.vol = int(100 / (self.w / divCurrW) - n)
        pygame.mixer_music.set_volume(self.vol / 100)


class SearchBar(object):
    def __init__(self, fWork: PygameMp3Player, callback, edgeColor=(128, 128, 128), insideColor=(164, 164, 164),
                 charColor=(255, 255, 255)):
        self.status = 1
        self.isDetected = False
        self.fw = fWork
        self.edge_clr = edgeColor
        self.inside_clr = insideColor
        self.char_clr = charColor
        self.x0, self.x1, = SCREEN_W - 430, SCREEN_W - 115
        self.w = 200
        self.h = 30
        self.y = 0  # 顶边
        self.edge_rect = pygame.Rect(self.x0 - 5, self.y - 16, self.w + 10, self.h + 20)
        self.rect_detect = pygame.Rect(self.x0, self.y - 16, self.x1 - self.x0, self.h)
        self.isInput = False
        self.textBox = TextBox(self.w, self.h - 5, self.x0, self.y + 3, self.fw.font18, callback, self.inside_clr,
                               self.char_clr)

    def mouse_motion(self, pos):
        if self.rect_detect.collidepoint(pos):
            self.isDetected = True
            return
        self.isDetected = False

    def mouse_up(self, pos, btn):
        if self.isDetected:
            self.isInput = True
        else:
            self.isInput = False
            self.isDetected = False

    def key_down(self, event):
        if self.isInput:
            self.textBox.safe_key_down(event)

    def show(self, scr: pygame.SurfaceType):
        if self.isDetected or self.isInput:
            pygame.draw.rect(scr, self.edge_clr, self.edge_rect)
        if self.isInput:
            self.textBox.show(scr)


class TextBox:
    def __init__(self, w, h, x, y, font=None, callback=None, insideColor=(0, 0, 0), charColor=(255, 255, 255)):
        """
        wheel from https://blog.csdn.net/qq_39687901/article/details/104684429
        :param w:文本框宽度
        :param h:文本框高度
        :param x:文本框坐标
        :param y:文本框坐标
        :param font:文本框中使用的字体
        :param callback:在文本框按下回车键之后的回调函数
        """
        self.width = w
        self.height = h
        self.x = x
        self.y = y
        self.text = ""  # 文本框内容
        self.callback = callback
        self.inside_clr = insideColor
        self.char_clr = charColor
        # 创建背景surface
        self.rect = pygame.rect.Rect(self.x, self.y, w, h)
        # 如果font为None,那么效果可能不太好，建议传入font，更好调节
        if font is None:
            self.font = pygame.font.SysFont('microsoftyaheimicrosoftyaheiui', 16)
        else:
            self.font = font
        self.dagparams = DefaultDagParams()
        self.state = 0  # 0初始状态 1输入拼音状态
        self.page = 1  # 第几页
        self.limit = 5  # 显示几个汉字
        self.pinyin = ''
        self.word_list = []  # 候选词列表
        self.word_list_surf = None  # 候选词surface
        self.buffer_text = ''  # 联想缓冲区字符串

    def create_word_list_surf(self):
        """
        创建联想词surface
        """
        word_list = [str(index + 1) + '.' + word for index, word in enumerate(self.word_list)]
        text = " ".join(word_list)
        self.word_list_surf = self.font.render(text, True, (255, 255, 255))

    def show(self, dest_surf):
        # 创建文字surf
        text_surf = self.font.render(self.text, True, self.char_clr)
        # 绘制背景色
        dest_surf.fill(self.inside_clr, self.rect)
        # 绘制文字
        dest_surf.blit(text_surf, (self.x, self.y + (self.height - text_surf.get_height())),
                       (0, 0, self.width, self.height))
        # 绘制联想词
        if self.state == 1:
            dest_surf.blit(self.word_list_surf,
                           (self.x, self.y + (self.height - text_surf.get_height()) + 30)
                           # ,(0, 0, self.width, self.height)
                           )

    def key_down(self, event):
        unicode = event.unicode
        key = event.key

        # 退位键
        if key == 8:
            self.text = self.text[:-1]
            if self.state == 1:
                self.buffer_text = self.buffer_text[:-1]
            return

        # 切换大小写键
        if key == 301:
            return

        # 回车键
        if key == 13:
            if self.callback:
                self.callback(self.text)
            return

        # ESC
        if key == 27:
            self.reset()
            return

        # print(key)
        # 空格输入中文
        if self.state == 1 and key == 32:
            self.state = 0
            self.text = self.text[:-len(self.buffer_text)] + self.word_list[0]
            self.word_list = []
            self.buffer_text = ''
            self.page = 1
            return

        # 翻页
        if self.state == 1 and key == 61:
            self.page += 1
            self.word_list = self.py2hz(self.buffer_text)
            if len(self.word_list) == 0:
                self.page -= 1
                self.word_list = self.py2hz(self.buffer_text)
            self.create_word_list_surf()
            return

        # 回退
        if self.state == 1 and key == 45:
            self.page -= 1
            if self.page < 1:
                self.page = 1
            self.word_list = self.py2hz(self.buffer_text)
            self.create_word_list_surf()
            return

        # 选字
        if self.state == 1 and key in (49, 50, 51, 52, 53):
            self.state = 0
            if len(self.word_list) <= key - 49:
                return
            self.text = self.text[:-len(self.buffer_text)] + self.word_list[key - 49]
            self.word_list = []
            self.buffer_text = ''
            self.page = 1
            return

        try:
            if unicode != "":
                char = unicode
            else:
                char = chr(key)
        except ValueError:
            return
        if char in string.ascii_letters:
            self.buffer_text += char
            self.word_list = self.py2hz(self.buffer_text)
            self.create_word_list_surf()
            # print(self.buffer_text)
            self.state = 1
        if char in string.ascii_letters or char in string.punctuation or char in string.digits:
            self.text += char

    def safe_key_down(self, event):
        try:
            self.key_down(event)
        except IndexError:  # 一定要写catch什么错 要不然到时候报什么错都不说明的... 比如代码莫名奇妙不执行...结果是因为div by zero
            self.reset()
            # traceback.print_exc()

    def py2hz(self, pinyin):
        result = dag(self.dagparams, (pinyin,), path_num=self.limit * self.page)[
                 (self.page - 1) * self.limit:self.page * self.limit]
        data = [item.path[0] for item in result]
        return data

    def reset(self):
        # 异常的时候还原到初始状态
        self.state = 0  # 0初始状态 1输入拼音状态
        self.page = 1  # 第几页
        self.limit = 5  # 显示几个汉字
        self.pinyin = ''
        self.word_list = []  # 候选词列表
        self.word_list_surf = None  # 候选词surface
        self.buffer_text = ''  # 联想缓冲区字符串


class ScrollBar(object):
    def __init__(self, x, page_all=-1, y0=0, y1=SCREEN_H, width=3, color=(102, 102, 102)):
        self.currPage = 0
        self.x = x
        self.y0, self.y1 = y0, y1
        self.w = width
        self.c = color
        if page_all == 0:
            page_all = 1
        self.barH = (y1 - y0) // page_all

    def set_new_page(self, new_page):
        self.currPage = 0
        if new_page == 0:
            self.barH = self.y1 - self.y0
            return
        self.barH = (self.y1 - self.y0) // new_page

    def show(self, scr: pygame.SurfaceType):
        pygame.draw.rect(scr, self.c, (self.x, self.currPage * self.barH + self.y0, self.w, self.barH))


"""
MANAGER
"""


class Music(object):
    def __init__(self, fWork: PygameMp3Player, musicPath=None, lrcPath=None, lrcTranPath=None):
        if musicPath is None:
            self.src = musicPath
            self.title = "啥都没有"
            self.album = "啥都没有"
            self.artist = "啥都没有"
            self.cover_data = ""
            self.lyric = None
            self.second = 0
            return
        self.src = musicPath
        self.tempPath = fWork.tempPath
        self.musicPath = musicPath
        self.fileName = str(os.path.basename(musicPath).split('.')[0])
        self.id3 = eyed3.load(musicPath)
        self.fw = fWork
        # 垃圾代码 有时间改 我也懒得改了...
        if self.id3.tag.title is None:
            self.title = self.fileName
        else:
            self.title = self.id3.tag.title
        if self.id3.tag.album is None:
            self.album = "啥都没有"
        else:
            self.album = self.id3.tag.album
        if self.id3.tag.artist is None:
            self.artist = "啥都没有"
        else:
            self.artist = self.id3.tag.artist
        if self.id3.tag.images:
            self.cover_data = self.id3.tag.images[0].image_data
        else:
            self.cover_data = None
        self.second = self.id3.info.time_secs
        # lyric logic
        self.isLyricInit = False
        self.lyric = None
        self.lyricDisplay = None
        self.lrcPath = lrcPath
        self.lrcTranPath = lrcTranPath

    def init_lyric(self):
        # lycPath = "lyric/" + self.fileName
        if not self.isLyricInit and musicPath is not None and self.lrcPath is not None:
            self.lyric = LyricContainer()
            self.lyric.init(self.lrcPath, self.lrcTranPath)
            self.lyricDisplay = LyricDisplayObjContainer(self.fw, self.lyric)  # For LyricDisplay
            self.isLyricInit = True
            print("load lyric finished!")

    def get_cover_file(self):
        if self.src is None or self.cover_data is None:
            return get_resource_path("img/None.png")
        salt = "pmp233"  # 喂 加什么盐呢? 这个不是密码加密!
        m = hashlib.md5()
        m.update((salt + self.title + self.artist + self.album).encode())
        destPath = self.tempPath + "/" + m.hexdigest()
        if os.path.exists(destPath):  # 如果已经存在(open函数会自动创建文件 一个坑)
            return destPath
        dest = open(destPath, "wb")  # 奇怪的命名方式
        dest.write(self.cover_data)
        dest.flush()
        dest.close()
        return dest.name

    def __str__(self):
        return self.src + " - " + self.title + " - " + self.album + " - " + self.artist + " - " + str(
            round(self.second, 3))


class PlayManager(object):
    """
    播放管理
    (推断没想好
    重构火葬场)
    """

    def __init__(self, fWork):
        self.fw = fWork
        self.isEmpty = False
        self.musicLst = []  # 当前正在播放的音乐在musicLst中的下标
        self.previousLst = []  # 用来记录以及播放过的音乐下标
        self.isPlay = False  # 是否正在播放
        self.currMusic = Music(fWork)  # 当前正在播放的音乐
        self.musicIndex = -1  # 当前正在播放的音乐在musicLst中的下标
        self.timeManager = MusicTimeManager(fWork)  # 时间刺客(误

    def play_next(self, orderNum, human_opera=True):
        """
        播放下一首歌
        :param orderNum:    顺序编号
        :param human_opera: 是否为人为操作
        """
        # 0=order, 1=loop, 2=rand
        if len(self.musicLst) == 0:
            return
        if self.musicIndex != -1:
            if orderNum != 1 or human_opera:  # 循环播放不加入列表(但人为操作可以)
                self.previousLst.append(self.musicIndex)  # 入栈
        if len(self.previousLst) == len(self.musicLst) and orderNum == 0:  # 为顺序播放
            self.previousLst.clear()
        print(self.previousLst)
        newIndex = self.get_next(orderNum, human_opera)
        self.switch(newIndex)
        print("next play:", newIndex)

    def play_previous(self):
        if len(self.musicLst) == 0:
            return
        if len(self.previousLst) == 0:  # 列表(栈)为空的处理
            if self.musicIndex == -1 or self.musicIndex == 0:  # 没有播放过(-1) 或者 已经previous到0
                self.previousLst.append(len(self.musicLst) - 1)  # 从最后一个开始 (入栈)
            else:  # 当前播放的歌不是最后一个
                self.previousLst.append(self.musicIndex - 1)  # 入栈
        self.switch(self.previousLst.pop())  # 出栈
        print(self.previousLst)

    def pause(self):
        pygame.mixer.music.pause()
        self.isPlay = False

    def unpause(self):
        if self.currMusic.src is not None:  # 如果什么歌都没播放 那就无视
            pygame.mixer.music.unpause()
            self.isPlay = True
            self.timeManager.sync()

    def get_next(self, orderNum, human_opera=False):
        """
        获取下一首歌
        :param orderNum: 顺序编号
        :param human_opera: 是否为人为操作
        :return: 下一首歌的下标
        """
        newIndex = 0
        if orderNum == 2:  # random, 绕开human_opera(其他写法我不想深入 大胆.jpg)
            while True:  # 如果随机后是重复的, 则重新随机
                newIndex = random.randint(0, len(self.musicLst) - 1)
                print("rand", newIndex)
                if newIndex != self.musicIndex or len(self.fw.manager.musicLst) <= 1:  # modify in v1.3 死循环
                    break
        elif orderNum == 0 or human_opera:  # order
            newIndex = (self.musicIndex + 1) % len(self.musicLst)
        elif orderNum == 1:  # loop
            newIndex = self.musicIndex
        return newIndex

    def switch(self, index):
        self.isPlay = True
        self.musicIndex = index
        self.currMusic = self.musicLst[self.musicIndex]
        self.currMusic: Music
        self.currMusic.init_lyric()
        pygame.mixer.music.load(self.currMusic.src)
        pygame.mixer.music.play()
        self.fw.manager.beginPlayMs = get_current_time_millis()
        self.fw.manager.timeManager.reset()
        self.fw.uiLst[UiEnum.playUi].lyricDisplay.update()
        print("currMusic change to", self.fw.manager.currMusic.title)


class MusicTimeManager(object):
    # 至于为什么不使用 pygame.mixer_music.get_pos() 是因为"返回的时间仅表示音乐播放了多长时间；它不考虑任何起始位置偏移。"
    # 计算播放进度: 现在的时间戳 - 开始播放时的时间戳
    # 当进度条发生改变只需要求出偏移量 并与beginPlayMs相减即可
    def __init__(self, fWork: PygameMp3Player):
        self.fw = fWork
        self.beginPlayMs = 0
        self.ms_played = 0

    def sync(self):
        """
        重新计算beginPlayMs (因为播放时间的原理是依靠时间戳来计算的 所以暂停等操作就需要重新计算来同步)
        """
        self.beginPlayMs = get_current_time_millis() - self.ms_played

    def change(self, sec):
        """
        更改播放条歌词显示进度
        :param sec: 新的播放进度(秒数)
        """
        ld = self.fw.uiLst[1].lyricDisplay  # 有点懒了改了,,,
        self.beginPlayMs -= (sec * 1000 - self.ms_played)  # 奇妙的更新播放进度
        if ld.lyricDisplay is None:  # 没有歌词不画
            return
        for pg in range(len(ld.lyricDisplay.containerWithPages)):
            if self.ms_played / 1000 >= ld.lyricDisplay.containerWithPages[pg][0].lyric.sec:
                ld.page_curr = pg
                ld.scrollBar.currPage = pg

    def update(self):
        """
        更新播放进度
        """
        self.ms_played = get_current_time_millis() - self.beginPlayMs

    def reset(self):
        """
        重置播放进度
        """
        self.beginPlayMs = get_current_time_millis()

    @staticmethod
    def update_location_mp3(sec):
        """
        更改音乐播放进度(mp3)
        :param sec 位置
        """
        pygame.mixer.music.rewind()
        pygame.mixer.music.set_pos(sec)


class ThemeManager(object):
    """
    如果有兴趣我还会写这功能
    """
    pass


"""
CONTROL
"""


class MusicList(object):
    """
    单个列表对象 (爸爸)
    """

    def __init__(self, fWork: PygameMp3Player, playUi, y, music: Music, index="", text=""):
        self.fw = fWork
        self.playUi = playUi
        self.music = music
        self.index = index
        self.text = text
        self.y = y
        self.btn = Button(self.fw, get_resource_path("img/btn/play/pause.bmp"), SCREEN_W - 75, self.y, self.btn_func)

    def show(self, scr: pygame.SurfaceType):
        theme = self.fw.theme
        # number
        img = self.fw.font32.render(self.index, True, theme.musicListUi_color_number)
        scr.blit(img, (30, self.y))
        # title
        img = self.fw.font25.render(self.text + self.music.title, True, theme.musicListUi_color_title)
        scr.blit(img, (90, self.y - 5))
        # album and singer
        img = self.fw.font12.render(self.music.artist + " - " + self.music.album, True,
                                    theme.musicListUi_color_subtitle)
        scr.blit(img, (90, self.y + 25))
        self.btn.show(scr)

    def btn_func(self):
        self.fw.manager.currMusic = self.music
        self.fw.manager.currMusic.init_lyric()
        pygame.mixer.music.load(self.music.src)
        pygame.mixer.music.play()
        self.fw.manager.timeManager.reset()
        self.playUi.lyricDisplay.update()
        self.playUi.playBar.sec_all = self.fw.manager.currMusic.second
        self.fw.manager.musicIndex = int(self.index) - 1  # 因为这里的下标是从1开始的
        self.fw.manager.isPlay = True


class SpecialMusicList(MusicList):
    """
    特殊的单个列表对象 (儿子)
    """

    def __init__(self, fWork: PygameMp3Player, playUi):
        super().__init__(fWork, playUi, 15, fWork.manager.currMusic, text="当前正在播放: ")

    def btn_func(self):
        self.playUi.playInfo.update()
        self.fw.status = UiEnum.playUi


class PlayInfoDisplay(object):

    def __init__(self, fWork: PygameMp3Player):
        self.fw = fWork
        self.cover = None
        self.title = None
        self.artist = None
        self.album = None
        self.update()

    def update(self):
        self.cover = pygame.transform.scale(pygame.image.load(self.fw.manager.currMusic.get_cover_file()), (320, 320))
        self.title = self.fw.manager.currMusic.title
        self.artist = self.fw.manager.currMusic.artist
        self.album = self.fw.manager.currMusic.album

    def show(self, scr):
        textSurface = self.fw.font32.render(self.title, True, self.fw.theme.playUi_color_title)
        w = textSurface.get_width()
        scr.blit(textSurface, (SCREEN_W / 2 - w / 2 + 192, SCREEN_H // 2 - 250))

        textSurface = self.fw.font20.render(self.artist + "-" + self.album, True, self.fw.theme.playUi_color_subtitle)
        w = textSurface.get_width()
        scr.blit(textSurface, (SCREEN_W / 2 - w / 2 + 192, SCREEN_H // 2 - 200))
        scr.blit(self.cover, (50, 150))


class LyricDisplay(object):
    def __init__(self, fWork: PygameMp3Player):
        self.fw = fWork
        self.scrollBar = ScrollBar(530 + 340, y0=233, y1=533)
        self.lyricDisplay: LyricDisplayObjContainer = None
        self.page_curr = 0
        self.has_play_page = 0
        self.isChangedPage = False
        self.rect = pygame.Rect(530, 233, 340, 300)

    def show(self, scr):
        if self.lyricDisplay is None:  # 没有歌词不画
            return
        sec_currPlayed = self.fw.manager.timeManager.ms_played / 1000
        # 换页判断
        # 条件: 当前页数不能为最后一页, 当前已播放秒数大于下一页的第一个歌词秒数
        # (由于and属于短路操作 所以如果第一个条件不成立则不会执行第二个)
        # if (not (self.page_curr + 1) >= len(self.lyricDisplay.containerWithPages)) and \
        #         sec_currPlayed >= self.lyricDisplay.containerWithPages[self.page_curr + 1][0].lyric.sec and \
        #         not sec_currPlayed >= self.lyricDisplay.containerWithPages[self.page_curr + 1][-1].lyric.sec:
        #     self.has_play_page += 1  # core
        for i in range(len(self.lyricDisplay.containerWithPages) - 1, -1, -1):
            if self.lyricDisplay.containerWithPages[i][0].lyric.sec <= sec_currPlayed <= \
                    self.lyricDisplay.containerWithPages[i][-1].lyric.sec:
                self.has_play_page = i
                break
        if self.isChangedPage and self.page_curr == self.has_play_page:
            self.isChangedPage = False
        if not self.isChangedPage:  # 判断是否该换页
            self.page_curr = self.has_play_page
        self.scrollBar.currPage = self.page_curr
        self.scrollBar.show(scr)

        currPageLst = self.lyricDisplay.containerWithPages[self.page_curr]
        hasChoose = False
        for i in range(len(currPageLst) - 1, -1, -1):  # 从结尾开始遍历来寻找选定歌词
            if sec_currPlayed >= currPageLst[i].lyric.sec and not hasChoose and self.has_play_page == self.page_curr:
                currPageLst[i].show(scr, True)
                hasChoose = True
                continue
            currPageLst[i].show(scr)

    def update(self):
        if self.fw.manager.isEmpty:
            return
        self.lyricDisplay = self.fw.manager.currMusic.lyricDisplay
        if self.lyricDisplay is None:  # 如果不存在不执行以下操作
            return
        self.page_curr = 0
        self.scrollBar.set_new_page(self.lyricDisplay.page_all)

    def mouse_down(self, pos, btn):
        if not self.rect.collidepoint(pos):
            return
        if btn == 1:
            if self.lyricDisplay is not None:
                for obj in self.lyricDisplay.containerWithPages[self.page_curr]:
                    obj.mouse_down(pos, btn)
        if btn == 4:  # 滚轮上滑
            if self.lyricDisplay is not None and self.page_curr == 0:
                return
            self.page_curr -= 1
            self.scrollBar.currPage = self.page_curr
            self.isChangedPage = True
        elif btn == 5:  # 滚轮下滑
            if self.lyricDisplay is not None and (self.page_curr + 1) >= self.lyricDisplay.page_all:
                return
            self.page_curr += 1
            self.scrollBar.currPage = self.page_curr
            self.isChangedPage = True

    def mouse_up(self, pos, btn):
        if btn == 1:
            if self.lyricDisplay is not None:
                for obj in self.lyricDisplay.containerWithPages[self.page_curr]:
                    if obj.mouse_up(pos, btn):
                        self.isChangedPage = False
                        for i in range(len(self.lyricDisplay.containerWithPages) - 1, -1, -1):
                            if self.fw.manager.timeManager.ms_played // 1000 >= \
                                    self.lyricDisplay.containerWithPages[i][0].lyric.sec:
                                self.has_play_page = i
                                break
                        self.page_curr = self.has_play_page

    def mouse_motion(self, pos):
        if self.lyricDisplay is not None:
            for obj in self.lyricDisplay.containerWithPages[self.page_curr]:
                obj.mouse_motion(pos)

    def key_up(self, key):
        if key == pygame.K_r:
            self.re_location()

    def re_location(self):
        """
        重新跳转到正在播放的歌词位置
        """
        self.isChangedPage = False
        self.page_curr = self.has_play_page


"""
UI
"""


class UiEnum(int, Enum):
    musicListUi = 0
    playUi = 1
    testUi = 2


class UI(object):
    def __init__(self, fWork: PygameMp3Player):
        self.btnLst = []
        self.fw = fWork

    def mouse_up(self, pos, btn):
        if btn == 1:  # 左键
            for b in self.btnLst:
                b.mouse_up(pos)

    def mouse_down(self, pos, btn):
        if btn == 1:  # 左键
            for b in self.btnLst:
                b.mouse_down(pos)

    def mouse_motion(self, pos):
        pass

    def key_down(self, event):
        pass

    def key_up(self, event):
        pass

    def show(self, scr: pygame.SurfaceType):
        for b in self.btnLst:
            b.show(scr)


class TestUI(UI):
    def __init__(self, fWork: PygameMp3Player):
        super().__init__(fWork)
        self.btnLst.append(
            Button(self.fw, get_resource_path("img/btn/play/up.bmp"), SCREEN_W // 2 - 20, 30, self.btn_func_test))

    def btn_func_test(self):
        self.fw.status = UiEnum.playUi


class MusicListUI(UI):
    def __init__(self, fWork: PygameMp3Player, playUi):
        super().__init__(fWork)
        # 页数 = ceil(总量 / 单页可放置量)
        self.playUi = playUi
        self.SINGLE_PAGE_MAX = 9
        # spec_musicList = math.ceil(len(self.fw.manager.musicLst) / self.SINGLE_PAGE_MAX)  # 每页上都会有一个”当前正在播放“对象
        # self.page_all = math.ceil((len(self.fw.manager.musicLst)) / self.SINGLE_PAGE_MAX)
        self.page_all = math.ceil(len(self.fw.manager.musicLst) / self.SINGLE_PAGE_MAX)
        if self.page_all == 0:
            self.page_all = 1
        # self.page_all += self.page_all - spec_musicList  # 可能还会再有一页
        self.page_curr = 0
        self.musicListObjLst = []
        self.specMusicListObj = SpecialMusicList(self.fw, playUi)
        self.scrollBar = ScrollBar(SCREEN_W - 4, self.page_all)
        self.searchBar = SearchBar(fWork, self.func_search)
        self.MUSIC_OBJ_LST = []  # 用于替换musicListObjLst
        self.PAGE_ALL = self.page_all
        self.temp_page_all = 0
        # LIST INIT
        i = 0
        # 这么繁琐的方式是因为有一个特殊的MusicList(当前正在播放)
        for p in range(self.page_all):  # 页数
            page = []
            # page_btn = [self.specMusicListObj.btn]
            y = 80
            for n in range(9):  # 一页的能存放个数
                if i == len(self.fw.manager.musicLst):
                    break
                musicObj = self.fw.manager.musicLst[i]
                mustListObj = MusicList(self.fw, self.playUi, y, musicObj, str(i + 1))
                page.append(mustListObj)
                # page_btn.append(mustListObj.btn)
                y += 80
                i += 1
            self.musicListObjLst.append(page)
            a: MusicList
            # self.btnLst.append(page_btn)
        self.MUSIC_OBJ_LST = self.musicListObjLst[:]

    def show(self, scr: pygame.SurfaceType):
        scr.fill(self.fw.theme.musicListUi_color_bg)
        self.scrollBar.show(scr)
        self.searchBar.show(scr)
        # 比较两个对象是否相同，如果不相同那么就是换歌了
        if self.fw.manager.currMusic != self.specMusicListObj.music:
            print("currMusic change to", self.fw.manager.currMusic.title)
            self.playUi.btnLst[2] = Button(self.fw, get_playPause_pic(self.fw.manager.isPlay), SCREEN_W // 2 - 30,
                                           SCREEN_H - 120,
                                           self.playUi.btn_func_pp)
            self.specMusicListObj.music = self.fw.manager.currMusic
        self.specMusicListObj.show(scr)
        if len(self.musicListObjLst) == 0:
            return
        for obj in self.musicListObjLst[self.page_curr]:
            obj.show(scr)

    def mouse_motion(self, pos):
        self.searchBar.mouse_motion(pos)

    def mouse_down(self, pos, btn):
        if btn == 1:  # 左键
            self.specMusicListObj.btn.mouse_down(pos)
            for listObj in self.musicListObjLst[self.page_curr]:
                listObj: MusicList
                listObj.btn.mouse_down(pos)
        elif btn == 5:  # 滚轮下滑
            if (self.page_curr + 1) >= self.page_all:
                return
            self.page_curr += 1
            self.scrollBar.currPage = self.page_curr
        elif btn == 4:  # 滚轮上滑
            if self.page_curr == 0:
                return
            self.page_curr -= 1
            self.scrollBar.currPage = self.page_curr

    def mouse_up(self, pos, btn):
        if btn == 1:  # 左键
            self.specMusicListObj.btn.mouse_up(pos)
            for listObj in self.musicListObjLst[self.page_curr]:
                listObj: MusicList
                listObj.btn.mouse_up(pos)
            self.searchBar.mouse_up(pos, btn)

    def key_down(self, event):
        self.searchBar.key_down(event)

    def func_search(self, content: str):
        # print("func_search 调用")
        if content == "":  # 当搜索为空时，默认为还原列表
            print("还原列表")
            self.musicListObjLst = self.MUSIC_OBJ_LST[:]
            self.page_all = self.PAGE_ALL
            self.scrollBar.set_new_page(self.PAGE_ALL)
            self.page_curr = 0
        else:
            print("搜索中...")
            content = content.lower()
            searchedLst = []
            pageLst = []
            mo: MusicList
            page_all = 0
            n = 1
            y = 80
            for iLst in self.MUSIC_OBJ_LST:
                for mo in iLst:
                    name = mo.music.title.lower()
                    if name.find(content) != -1:
                        if len(pageLst) == self.SINGLE_PAGE_MAX:
                            searchedLst.append(pageLst)
                            page_all += 1
                            y = 80
                            pageLst = []  # 不能调用clear() 因为地址传递性
                        else:
                            pageLst.append(MusicList(self.fw, self.playUi, y, mo.music, str(n)))
                            y += 80
                            n += 1
            # if len(pageLst) != 0:  # 如果搜索到的内容不大于1页就需要再append下
            # FIXED: 如果没有搜索到任何东西也要添加一页 否则会out of index
            searchedLst.append([])
            page_all += 1
            self.page_all = page_all
            self.page_curr = 0
            self.scrollBar.page_curr = 0
            self.musicListObjLst = searchedLst
            self.scrollBar.set_new_page(page_all)
            print("搜索 done!")


class PlayUI(UI):
    def __init__(self, fWork: PygameMp3Player):
        super().__init__(fWork)
        self.playInfo = PlayInfoDisplay(fWork)
        self.lyricDisplay = LyricDisplay(fWork)
        self.playBar = PlayBar(fWork)
        self.volumeBar = VolumeBar(fWork)
        # 0=order, 1=loop, 2=rand
        self.orderNum = 0
        """
        control init
        """
        self.btnLst.append(  # 0
            Button(self.fw, get_resource_path("img/btn/play/up.bmp"), SCREEN_W // 2 - 20, 30, self.btn_func_return))
        self.btnLst.append(  # 1
            Button(self.fw, get_resource_path("img/btn/play/previous.bmp"), SCREEN_W // 2 - 160, SCREEN_H - 120,
                   self.btn_func_previous))
        self.btnLst.append(  # 2
            Button(self.fw, get_playPause_pic(self.fw.manager.isPlay), SCREEN_W // 2 - 30, SCREEN_H - 120,
                   self.btn_func_pp))
        self.btnLst.append(  # 3
            Button(self.fw, get_resource_path("img/btn/play/next.bmp"), SCREEN_W // 2 + 100, SCREEN_H - 120,
                   self.btn_func_next))
        self.btnLst.append(  # 4
            Button(self.fw, get_resource_path("img/btn/order/0.png"), SCREEN_W // 2 - 450, SCREEN_H - 120,
                   self.btn_func_order,
                   (255, 255, 255)))

    def show(self, scr: pygame.SurfaceType):
        scr.fill(self.fw.theme.playUi_color_bg)
        if pygame.mixer_music.get_busy() == 0 and self.fw.manager.isPlay:
            self.fw.manager.play_next(self.orderNum, False)
            self.update()
        self.lyricDisplay.show(scr)
        self.playInfo.show(scr)
        self.playBar.show(scr)
        self.volumeBar.show(scr)
        for b in self.btnLst:
            b.show(scr)

    def mouse_down(self, pos, btn):
        for b in self.btnLst:
            b.mouse_down(pos)
        self.playBar.mouse_down(pos, btn)
        self.volumeBar.mouse_down(pos, btn)
        self.lyricDisplay.mouse_down(pos, btn)

    def mouse_up(self, pos, btn):
        for b in self.btnLst:
            b.mouse_up(pos)
        self.playBar.mouse_up(pos, btn)
        self.volumeBar.mouse_up(pos, btn)
        if self.fw.manager.isEmpty:
            return
        self.lyricDisplay.mouse_up(pos, btn)

    def mouse_motion(self, pos):
        self.playBar.mouse_motion(pos)
        self.volumeBar.mouse_motion(pos)
        self.lyricDisplay.mouse_motion(pos)

    def key_up(self, event):
        self.lyricDisplay.key_up(event)

    def btn_func_return(self):
        self.fw.status = UiEnum.musicListUi

    def btn_func_pp(self):
        if self.fw.manager.isPlay:
            self.fw.manager.pause()
        else:
            self.fw.manager.unpause()
        self.btn_change()

    def btn_func_previous(self):
        if self.fw.manager.isEmpty:
            return
        self.fw.manager.play_previous()
        self.update()

    def btn_func_next(self):
        if self.fw.manager.isEmpty:
            return
        self.fw.manager.play_next(self.orderNum)
        self.update()

    def btn_func_order(self):  # 0=order, 1=loop, 2=rand
        self.orderNum = (self.orderNum + 1) % 3
        self.btnLst[4].__init__(self.fw, get_resource_path("img/btn/order/" + str(self.orderNum) + ".png"),
                                SCREEN_W // 2 - 450,
                                SCREEN_H - 120, self.btn_func_order, (255, 255, 255))

    def btn_func_test(self):
        self.fw.status = UiEnum.testUi

    def btn_change(self):
        self.btnLst[2].__init__(self.fw, get_playPause_pic(self.fw.manager.isPlay), SCREEN_W // 2 - 30, SCREEN_H - 120,
                                self.btn_func_pp)

    def update(self):
        """
        更新控件状态
        """
        self.btn_change()
        self.playInfo.update()
        self.playBar.sec_all = self.fw.manager.currMusic.second
        self.lyricDisplay.update()


"""
Lyric
"""


class Lyric(object):
    """
    lrc文件中的一行
    """

    def __init__(self, sec, text, text_tran=""):
        self.sec = sec
        self.text = text
        self.text_tran = text_tran


class LyricDisplayObj(object):
    """
    Lyric显示的单行对象
    """

    def __init__(self, fWork: PygameMp3Player, clicked_func, lyric: Lyric, x, y):
        self.fw = fWork
        self.lyric = lyric
        self.img_text = fWork.font20.render(lyric.text, True, self.fw.theme.playUi_color_lyric_main_unfocused)
        self.img_text_selected = fWork.font20.render(lyric.text, True, self.fw.theme.playUi_color_lyric_main_focus)
        self.img_text_tran = fWork.font12.render(lyric.text_tran, True, self.fw.theme.playUi_color_lyric_sub_unfocused)
        self.img_text_tran_selected = fWork.font12.render(lyric.text_tran, True,
                                                          self.fw.theme.playUi_color_lyric_sub_focus)
        self.x, self.y = x - self.img_text.get_width() / 2, y
        self.x_tran = x - self.img_text_tran.get_width() / 2
        text_tran_h = self.img_text_tran.get_height()
        if lyric.text_tran == "":
            text_tran_h = 0
        self.rect = pygame.rect.Rect(self.x, y, max(self.img_text.get_width(), self.img_text_tran.get_width()),
                                     self.img_text.get_height() + text_tran_h)
        self.clicked_func = clicked_func
        self.needDrawRect = False
        self.status = 0

    def show(self, scr: pygame.SurfaceType, is_selected=False):
        # pygame.draw.rect(scr, (102, 204, 255), self.rect)
        if self.needDrawRect:
            pygame.draw.rect(scr, (96, 96, 96), self.rect)
        if is_selected:
            scr.blit(self.img_text_selected, (self.x, self.y))
            scr.blit(self.img_text_tran_selected, (self.x_tran, self.y + 25))
            return
        scr.blit(self.img_text, (self.x, self.y))
        scr.blit(self.img_text_tran, (self.x_tran, self.y + 25))

    def mouse_down(self, pos, btn):
        if not self.rect.collidepoint(pos):
            return
        self.status = 1

    def mouse_up(self, pos, btn):
        if not self.rect.collidepoint(pos):
            return False
        self.clicked_func(self.lyric.sec)
        self.status = 0
        return True

    def mouse_motion(self, pos):
        if not self.rect.collidepoint(pos):
            self.needDrawRect = False
            return
        self.needDrawRect = True


"""
CONTAINER
"""


class LyricContainer(object):
    """
    存储Lyric对象的容器
    该容器相当于一个lrc文件
    """

    def __init__(self):
        self.src = ""
        self.src_tran = ""
        self.container = []
        self.has_tran = False
        self.length = 0

    def init(self, srcPath, srcPath_tran=None):
        if srcPath_tran is not None:
            self.has_tran = True
        self.container = get_Lyric_list(srcPath, srcPath_tran)
        self.length = len(self.container)


class LyricDisplayObjContainer(object):
    """
    存储Lyric对象用于显示的容器
    """

    def __init__(self, fWork: PygameMp3Player, lyricContainer: LyricContainer):
        self.ONE_PAGE_MAX = 6
        self.fw = fWork
        self.lyricContainer = lyricContainer
        self.has_tran = lyricContainer.has_tran
        self.containerWithPages = []
        self.page_all = math.ceil(self.lyricContainer.length / self.ONE_PAGE_MAX)
        Y_OFFSET = 50
        Y_ORIGINAL = 233
        lrc: Lyric
        i = 0
        for p in range(self.page_all):
            page = []
            y = Y_ORIGINAL
            for n in range(6):
                if i == len(self.lyricContainer.container):
                    break
                page.append(
                    LyricDisplayObj(self.fw, self.clicked_func, lyricContainer.container[i], 700, y))
                i += 1
                y += Y_OFFSET
            self.containerWithPages.append(page)

    def clicked_func(self, sec):
        self.fw.manager.timeManager.change(sec)
        self.fw.manager.timeManager.update_location_mp3(sec)
        self.fw.manager.timeManager.update()


"""
UTIL
"""


def get_playPause_pic(isPlay):
    if isPlay:
        return get_resource_path("img/btn/play/play.bmp")
    return get_resource_path("img/btn/play/pause.bmp")


def get_current_time_millis():
    return int(round(time.time() * 1000))


def get_lrc_time_text(s):
    """
    获取单行lrc数据
    :param s: 单行lrc文本
    :return: (分, 秒, 毫秒, 歌词)
    """
    pattern = re.compile("\\[(\\d{1,2}):(\\d{1,2}).(\\d{1,3})]([\\s\\S]*)")
    match = pattern.match(s)
    if match is None:
        return None
    return match.group(1), match.group(2), match.group(3), match.group(4)


def convert_to_minute(sec):
    if sec <= 0:
        m, s = "00", "00"
    else:
        m, s = divmod(sec, 60)
        m, s = str(int(m)), str(int(s))
        if len(m) <= 1:
            m = "0" + m
        if len(s) <= 1:
            s = "0" + s
    return m + ":" + s


def convert_to_sec(m, s, ms):
    m = int(m)
    s = int(s)
    ms = int(ms)
    return m * 60 + s + ms / 1000


def get_Lyric_list(filePath, filePath_tran=None):
    """
    获取Lyric对象的列表
    :param filePath: lrc文件路径
    :param filePath_tran: 翻译的lrc文件路径(默认为None)
    :return: 一个Lyric对象的列表
    """
    fObj = open(filePath, 'r', encoding='utf-8')
    lines = fObj.readlines()
    fObj.close()
    lines_tran = None
    if filePath_tran is not None:
        fObj = open(filePath_tran, 'r', encoding='utf-8')
        lines_tran = fObj.readlines()
        fObj.close()
    ansLst = []
    i = 0
    for line in lines:  # 以主歌词为基准
        temp: tuple = get_lrc_time_text(line)
        if temp is None:
            continue
        m, s, ms, text = temp
        text = text.rstrip("\n")
        sec = convert_to_sec(m, s, ms)

        if lines_tran is not None:
            text_tran = get_lrc_time_text(lines_tran[i])[3]
            text_tran = text_tran.rstrip("\n")
        else:  # 如果主歌词为空行(比如: [xx:xx.xx] ) 那么副歌词可能就不会有相关行, 导致不同步 (网易云歌词格式) 详见 lyric/Reference(_tran).lrc文件
            ansLst.append(Lyric(sec, text))
            continue
        ansLst.append(Lyric(sec, text, text_tran))
        i += 1
    return ansLst


def _no_bug_plz():
    try:
        noBug = open("NOBUG.txt", encoding='UTF-8')
        noBugLineLst = noBug.readlines()
        for s in noBugLineLst:
            print(s, end='')
        print('\n')
    except FileNotFoundError:
        print("尻文件不见了 还我神兽 o(╥﹏╥)o\n")


def check_file(folderLst: list):
    """
    检查文件夹存在性
    """
    for name in folderLst:
        if not os.path.exists(name):
            os.makedirs(name)


def get_resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        absolute_path = os.path.join(sys._MEIPASS, relative)
    else:
        absolute_path = os.path.join(relative)
    return absolute_path


# _no_bug_plz()

# musicPath = get_path("music folder path: ", "music")
# lyricPath = get_path("lyric folder path: ", "lyric")
ININAME = "PygameMp3Player.ini"
config = configparser.ConfigParser()
tempPath = "temp"
musicPath = "music"
lyricPath = "lyric"


def _do_ini_init(fName):
    with open(ININAME, 'w', 'UTF-8') as destF:
        config.add_section("folder")
        config.set("folder", "temp", tempPath)
        config.set("folder", "music", musicPath)
        config.set("folder", "lyric", lyricPath)
        config.write(destF)


if not os.path.exists(ININAME):  # ini 不存在
    f = open(ININAME, 'w', encoding='UTF-8')
    config.add_section("folder")
    config.set("folder", "temp", tempPath)
    config.set("folder", "music", musicPath)
    config.set("folder", "lyric", lyricPath)
    config.write(f)
    f.close()
else:
    config.read(ININAME, encoding="utf-8")
    try:
        tempPath = config.get("folder", "temp")
        musicPath = config.get("folder", "music")
        lyricPath = config.get("folder", "lyric")
    except configparser.NoSectionError:
        print("Some sections are gone in PygameMp3Player.ini, plz check or remove file and run the program.")
        sys.exit()
    except configparser.NoOptionError:
        print("Some options are gone in PygameMp3Player.ini, plz check or remove file and run the program.")
        traceback.print_exc()
check_file([tempPath, musicPath, lyricPath])

pmp = PygameMp3Player(tempPath, musicPath, lyricPath, len(os.listdir(musicPath)) == 0)
print("共有歌曲数: ", len(pmp.manager.musicLst))

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.MOUSEBUTTONDOWN:
            pmp.mouse_down(e.pos, e.button)
        elif e.type == pygame.MOUSEBUTTONUP:
            pmp.mouse_up(e.pos, e.button)
        elif e.type == pygame.MOUSEMOTION:
            pmp.mouse_motion(e.pos)
        elif e.type == pygame.KEYDOWN:
            pmp.key_down(e)
        elif e.type == pygame.KEYUP:
            pmp.key_up(e)
    pmp.show()
