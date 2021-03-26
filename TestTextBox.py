import string

import pygame
from Pinyin2Hanzi import DefaultDagParams
from Pinyin2Hanzi import dag


# https://blog.csdn.net/qq_39687901/article/details/104684429
class TextBox:
    def __init__(self, w, h, x, y, font=None, callback=None):
        """
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
        # 创建背景surface
        self.__surface = pygame.Surface((w, h))
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

    def draw(self, dest_surf):
        # 创建文字surf
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        # 绘制背景色
        dest_surf.blit(self.__surface, (self.x, self.y))
        # 绘制文字
        dest_surf.blit(text_surf, (self.x, self.y + (self.height - text_surf.get_height())),
                       (0, 0, self.width, self.height))
        # 绘制联想词
        if self.state == 1:
            dest_surf.blit(self.word_list_surf,
                           (self.x, self.y + (self.height - text_surf.get_height()) - 30),
                           (0, 0, self.width, self.height)
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

        if unicode != "":
            char = unicode
        else:
            char = chr(key)

        if char in string.ascii_letters:
            self.buffer_text += char
            self.word_list = self.py2hz(self.buffer_text)
            self.create_word_list_surf()
            # print(self.buffer_text)
            self.state = 1
        self.text += char

    def safe_key_down(self, event):
        try:
            self.key_down(event)
        except:
            self.reset()

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


def callback(text):
    print("回车测试", text)


def main():
    # 英文文本框demo
    pygame.init()
    winSur = pygame.display.set_mode((640, 480))
    # 创建文本框
    text_box = TextBox(200, 30, 200, 200, callback=callback)

    # 游戏主循环
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.KEYDOWN:
                # 调用文本框键盘按下事件
                text_box.safe_key_down(event)
        pygame.time.delay(33)
        winSur.fill((0, 50, 0))
        # 绘制文本框
        text_box.draw(winSur)
        pygame.display.flip()


if __name__ == '__main__':
    main()
