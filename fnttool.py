#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import shutil
import sys
import datetime
import errno

from PIL import Image

"""{
  "info":
      {"face":"This is the name of the true type font.",
        "size":"The size of the true type font.",
        "bold":"The font is bold.",
        "italic":"The font is italic.",
        "charset":"The name of the OEM charset used (when not unicode).",
        "unicode":"Set to 1 if it is the unicode charset.",
        "stretchH":"The font height stretch in percentage. 100% means no stretch.",
        "smooth":"Set to 1 if smoothing was turned on.",
        "aa":"The supersampling level used. 1 means no supersampling was used.",
        "padding":"The padding for each character (up, right, down, left).",
        "spacing":"The spacing for each character (horizontal, vertical).",
        "outline":"The outline thickness for the characters."},
  "common":
      {"lineHeight":"This is the distance in pixels between each line of text.",
        "base":"The number of pixels from the absolute top of the line to the base of the characters.",
        "scaleW":"The width of the texture, normally used to scale the x pos of the character image.",
        "scaleH":"The height of the texture, normally used to scale the y pos of the character image.",
        "pages":"The number of texture pages included in the font.",
        "packed":"Set to 1 if the monochrome characters have been packed into each of the texture channels. In this case alphaChnl describes what is stored in each channel.",
        "alphaChnl":"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.",
        "redChnl":"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.",
        "greenChnl":"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.",
        "blueChnl":"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one."},
  "page":
      {"id":"The page id.",
        "file":"The texture file name."},
  "chars":
      {"count":"The number of chars does the fnt file hold."},
  "char":
      {"id":"The character id.",
          "x":"The left position of the character image in the texture.",
          "y":"The top position of the character image in the texture.",
          "width":"The width of the character image in the texture.",
          "height":"The height of the character image in the texture.",
          "xoffset":"How much the current position should be offset when copying the image from the texture to the screen.",
          "yoffset":"How much the current position should be offset when copying the image from the texture to the screen.",
          "xadvance":"How much the current position should be advanced after drawing the character.",
          "page":"The texture page where the character image is found.",
          "chnl":"The texture channel where the character image is found (1 = blue, 2 = green, 4 = red, 8 = alpha, 15 = all channels)."}
}"""

def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print(err)
    return out

def self_install(file, des):
    file_path = os.path.realpath(file)

    filename = file_path

    pos = filename.rfind("/")
    if pos:
        filename = filename[pos + 1:]

    pos = filename.find(".")
    if pos:
        filename = filename[:pos]

    to_path = os.path.join(des, filename)

    print("installing [" + file_path + "] \n\tto [" + to_path + "]")
    if os.path.isfile(to_path):
        os.remove(to_path)

    shutil.copy(file_path, to_path)
    run_cmd(['chmod', 'a+x', to_path])

def mkdir_p(path):
    # print("mkdir_p: " + path)
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
            
def get_img(path):
    try:
        img = Image.open(path)
    except:
        print ("get_act_img: file [" + path + "] is not valid image, skipped.")
        return None
    
    x = img.size[0]
    y = img.size[1]
    rgb_img = img.convert('RGBA')

    xSetFlag = True
    xLeft = 0
    xRight = x
    for x0 in range(0, x):
        yIsTranparent = True
        for y0 in range(0, y):
            pix = rgb_img.getpixel((x0, y0))
            if pix[3] != 0:
                yIsTranparent = False
                break
        if x0 > xLeft and yIsTranparent and xSetFlag:
            xLeft = x0
        if not xSetFlag and yIsTranparent and x0 < xRight:
            xRight = x0
            break
        if not yIsTranparent:
            xSetFlag = False

    ySetFlag = True
    yTop = y
    yBottom = 0
    for y0 in range(0, y):
        xIsTranparent = True
        for x0 in range(0, x):
            pix = rgb_img.getpixel((x0, y0))
            if pix[3] != 0:
                xIsTranparent = False
                break
        if y0 > yBottom and xIsTranparent and ySetFlag:
            yBottom = y0
        if not ySetFlag and xIsTranparent and y0 < yTop:
            yTop = y0
            break
        if not xIsTranparent:
            ySetFlag = False

    trueW = xRight - xLeft
    trueH = yTop - yBottom
    
    newImg = Image.new('RGBA', (trueW, trueH), (0, 0, 0, 0))

    newImg.paste(img, (-xLeft, -yBottom))

    return newImg
    
def makeFnt(imgList, cellW, cellH, width, height, desPath, lineCnt):
    strFnt = "info face=\"Arial\" size=" + str(cellH) + " bold=0 italic=0 charset=\"\" unicode=0 stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=2,2\n"
    strFnt += "common lineHeight=" + str(cellH) + " base=20 scaleW=" + str(width) + " scaleH=" + str(height) + " pages=1 packed=0\n"
    pre, fn = os.path.split(desPath)
    strFnt += "page id=0 file=\"" + fn + ".png\"\n"
    strFnt += "chars count=" + str(len(imgList)) + "\n"

    keyList = imgList.keys()
    keyList.sort()

    desImg = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    left = 0
    top = 0
    for i in xrange(0, len(keyList)):
        key = keyList[i]
        img = imgList[key]

        w = img.size[0]
        h = img.size[1]

        charCode = ord(str(key).decode("utf8"))

        x = (int)(left + ((cellW - w) / 2))
        y = (int)(top + ((cellH - h) / 2))

        desImg.paste(img, (x, y, x + w, y + h))

        strFnt += "char id=" + str(charCode) + " x=" + str(x) + " y=" + str(top) + " width=" + str(w) + " height=" + str(cellH) + " xoffset=0 yoffset=0 xadvance=" + str(w) + " page=0 chnl=0 letter=\"" + key + "\"\n"

        if i != 0 and i % lineCnt == 0:
            left = 0
            top += cellH
        else:
            left += cellW

    desImg.save(desPath + ".png")

    f = open(desPath + ".fnt", "wb")
    f.write(strFnt)
    f.close()

def main():

    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("fnttool.py", "/usr/local/bin")
        return

    _folder = ""
    _ext = ""
    _des = ""
    _width = 1024

    idx = 1
    while idx < len(sys.argv):
        cmd_s = sys.argv[idx]
        if cmd_s[0] == "-":
            cmd = cmd_s[1:]
            v = sys.argv[idx + 1]
            if cmd == "f":
                _folder = str(v)
                if not _folder.startswith("/"):
                    _folder = os.path.join(os.getcwd(), _folder)
            elif cmd == "e":
                _ext = str(v).lower()
            elif cmd == "d":
                _des = str(v)
                if not _des.startswith("/"):
                    _des = os.path.join(os.getcwd(), _des)
                if _des.lower().endswith(".png") or _des.lower().endswith(".fnt"):
                    _des = _des[:len(_des) - 4]
            elif cmd == "w":
                _width = v
            idx += 2
        else:
            idx += 1

    if _folder == "":
        print("\n***** fnttool *****")
        print("\t参数:")
        print("\t-f folder_path\t\tUsing files in folder 使用文件夹内的文件")
        print("\t-e extension\t\tOnly use files with specified extension 文件夹内仅搜索这类扩展名")
        print("\t-d filename\t\tDestination file name 指定创建的fnt文件名")
        print("\t-w max_width\t\tSet the fnt png image's max width 创建的fnt图片文件最大宽度，默认1024")

        return

    imgList = {}
    
    cellW = 0
    cellH = 0
    
    if os.path.isdir(_folder):
        # work
        sub_files = os.listdir(_folder)
        
        for fn in sub_files:
            file_path = os.path.join(_folder, fn)
            if os.path.isfile(file_path):
                if (_ext == "") or (fn.lower().endswith(_ext)):
                    name = fn[:fn.rfind(".")]
                    img = get_img(file_path)
                    if img != None:
                        imgList[name] = img

                        if (cellW < img.size[0]):
                            cellW = img.size[0]
                        if (cellH < img.size[1]):
                            cellH = img.size[1]
                    
    if len(imgList) <= 0:
        print("\n***** fnttool *****")
        print("\t参数:")
        print("\t-f folder_path\t\tUsing files in folder 使用文件夹内的文件")
        print("\t-e extension\t\tOnly use files with specified extension 文件夹内仅搜索这类扩展名")
        print("\t-d filename\t\tDestination file name 指定创建的fnt文件名")
        print("\t-w max_width\t\tSet the fnt png image's max width 创建的fnt图片文件最大宽度，默认1024")

        return

    pageWidth = 0
    pageHeight = 0
    
    lineCnt = (_width - (_width % cellW)) / cellW
    cellCnt = len(imgList)
    
    if cellCnt > lineCnt:
        if cellCnt % lineCnt > 0:
            cnt = (cellCnt - (cellCnt % lineCnt)) / lineCnt + 1
        else:
            cnt = (cellCnt - (cellCnt % lineCnt)) / lineCnt
        pageWidth = _width
        pageHeight = cellH * cnt
    else:
        pageWidth = cellW * cellCnt
        pageHeight = cellH

    if _des == "":
        _des = _folder

    makeFnt(imgList, cellW, cellH, pageWidth, pageHeight, _des, lineCnt)
    

if __name__ == "__main__":
    main()