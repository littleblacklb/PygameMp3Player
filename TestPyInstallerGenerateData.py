# [('bg.jpeg', 'D:\\mycode\\bg.jpeg', 'DATA'), ('bg2.jpeg', 'D:\\mycode\\bg2.jpeg', 'DATA')]
import os

fileLst = []


def rec_files(path):
    lsdir = os.listdir(path)
    dirs = [i for i in lsdir if os.path.isdir(os.path.join(
        path, i))]
    if dirs:
        for i in dirs:
            rec_files(os.path.join(path, i))
    for i in lsdir:
        name = os.path.join(path, i)
        if os.path.isfile(name):
            fileLst.append(name)


PATH1 = "img"
PATH2 = "font"
rec_files(PATH1)
rec_files(PATH2)
ansLst = []
for ph in fileLst:
    ansLst.append((ph, ph, 'DATA'))
print(ansLst)