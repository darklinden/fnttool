#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import shutil
import sys
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
        "packed":"Set to 1 if the monochrome characters have been packed into each of the texture channels.
            In this case alphaChnl describes what is stored in each channel.",
        "alphaChnl":"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 
            2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.",
        "redChnl":"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 
            2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.",
        "greenChnl":"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 
            2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.",
        "blueChnl":"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 
            2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one."},
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
          "xoffset":"How much the current position should be offset when copying the image 
                from the texture to the screen.",
          "yoffset":"How much the current position should be offset when copying the image 
                from the texture to the screen.",
          "xadvance":"How much the current position should be advanced after drawing the character.",
          "page":"The texture page where the character image is found.",
          "chnl":"The texture channel where the character image is found 
                (1 = blue, 2 = green, 4 = red, 8 = alpha, 15 = all channels)."}
}"""


def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print(err)
    return out


def self_install(fname, des):
    file_path = os.path.realpath(fname)

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


def get_img(path, alpha_control):
    try:
        img = Image.open(path)
    except:
        print ("get_act_img: file [" + path + "] is not valid image, skipped.")
        return None

    if alpha_control == 0:
        return img

    x = img.size[0]
    y = img.size[1]
    rgb_img = img.convert('RGBA')

    x_left = x
    x_right = 0
    for x0 in range(0, x):
        y_is_tranparent = True
        for y0 in range(0, y):
            pix = rgb_img.getpixel((x0, y0))
            if pix[3] != 0:
                y_is_tranparent = False
                break
        if not y_is_tranparent:
            if x0 < x_left:
                x_left = x0 - 1
            if x0 > x_right:
                x_right = x0 + 1

    if x_left < 0:
        x_left = 0
    if x_right > x:
        x_right = x

    y_top = 0
    y_bottom = y
    for y0 in range(0, y):
        x_is_tranparent = True
        for x0 in range(0, x):
            pix = rgb_img.getpixel((x0, y0))
            if pix[3] != 0:
                x_is_tranparent = False
                break
        if not x_is_tranparent:
            if y0 < y_bottom:
                y_bottom = y0 - 1
            if y0 > y_top:
                y_top = y0 + 1

    if y_bottom < 0:
        y_bottom = 0
    if y_top > y:
        y_top = y

    true_w = x_right - x_left
    true_h = y_top - y_bottom

    new_img = Image.new('RGBA', (true_w, true_h), (0, 0, 0, 0))

    new_img.paste(img, (-x_left, -y_bottom))

    return new_img


def make_fnt(img_list, cell_w, char_width_offset, cell_h, width, height, des_path, line_cnt):
    str_fnt = "info face=\"Arial\" size=" + str(
        cell_h) + " bold=0 italic=0 charset=\"\" unicode=0 stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=2,2\n"
    str_fnt += "common lineHeight=" + str(cell_h) + " base=20 scaleW=" + str(width) + " scaleH=" + str(
        height) + " pages=1 packed=0\n"
    pre, fn = os.path.split(des_path)
    str_fnt += "page id=0 file=\"" + fn + ".png\"\n"
    str_fnt += "chars count=" + str(len(img_list) + 1) + "\n"

    key_list = img_list.keys()
    key_list.sort()

    des_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    str_fnt += "char id=32 x=0 y=0 width=0 height=0 xoffset=0 yoffset=0 xadvance=" + str(
        cell_w + char_width_offset) + " page=0 chnl=0 letter=\"space\"\n"

    left = 0
    top = 0
    line_no = 0
    for i in xrange(0, len(key_list)):
        key = key_list[i]
        img = img_list[key]

        w = img.size[0]
        h = img.size[1]

        char_code = ord(str(key).decode("utf8"))

        x = int(left + ((cell_w - w) / 2))
        y = int(top + ((cell_h - h) / 2))

        des_img.paste(img, (x, y, x + w, y + h))

        str_fnt += "char id=" + str(char_code) + " x=" + str(x) + " y=" + str(top) + " width=" + str(w) + " height=" + \
                   str(cell_h) + " xoffset=0 yoffset=0 xadvance=" + str(w + char_width_offset) + \
                   " page=0 chnl=0 letter=\"" + key + "\"\n"

        line_no += 1
        if line_no < line_cnt:
            left += cell_w
        else:
            line_no = 0
            left = 0
            top += cell_h

    des_img.save(des_path + ".png")

    f = open(des_path + ".fnt", "wb")
    f.write(str_fnt)
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
    _char_width_offset = 0
    _alpha_control = 0

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
            elif cmd == "a":
                _alpha_control = int(str(v))
            elif cmd == "cw":
                _char_width_offset = int(str(v))
            idx += 2
        else:
            idx += 1

    if _folder == "":
        print("\n***** fnttool *****")
        print("\t参数:")
        print("\t-f folder_path\t\tUsing files in folder 使用文件夹内的文件")
        print("\t-e extension\t\tOnly use files with specified extension 文件夹内仅搜索这类扩展名")
        print("\t-a 0: 使用图片大小 [default] 1: 使用alpha中心大小")
        print("\t-d filename\t\tDestination file name 指定创建的fnt文件名")
        print("\t-w max_width\t\tSet the fnt png image's max width 创建的fnt图片文件最大宽度，默认1024")
        print("\t-cw char_width_offset\t\tSet the fnt png image's char width offset 创建的fnt图片单字间距，默认0")

        return

    img_list = {}

    cell_w = 0
    cell_h = 0

    if os.path.isdir(_folder):
        # work
        sub_files = os.listdir(_folder)

        for fn in sub_files:
            file_path = os.path.join(_folder, fn)
            if os.path.isfile(file_path):
                if fn == ".DS_Store":
                    continue
                if (_ext == "") or (fn.lower().endswith(_ext)):
                    name = fn[:fn.rfind(".")]
                    img = get_img(file_path, _alpha_control)
                    if img is not None:
                        img_list[name] = img

                        if cell_w < img.size[0]:
                            cell_w = img.size[0]
                        if cell_h < img.size[1]:
                            cell_h = img.size[1]

    if len(img_list) <= 0:
        print("\n***** fnttool *****")
        print("\t参数:")
        print("\t-f folder_path\t\tUsing files in folder 使用文件夹内的文件")
        print("\t-e extension\t\tOnly use files with specified extension 文件夹内仅搜索这类扩展名")
        print("\t-a 0: 使用图片大小 [default] 1: 使用alpha中心大小")
        print("\t-d filename\t\tDestination file name 指定创建的fnt文件名")
        print("\t-w max_width\t\tSet the fnt png image's max width 创建的fnt图片文件最大宽度，默认1024")
        print("\t-cw char_width_offset\t\tSet the fnt png image's char width offset 创建的fnt图片单字间距，默认0")

        return

    line_cnt = (_width - (_width % cell_w)) / cell_w
    cell_cnt = len(img_list)

    if cell_cnt > line_cnt:
        if cell_cnt % line_cnt > 0:
            cnt = (cell_cnt - (cell_cnt % line_cnt)) / line_cnt + 1
        else:
            cnt = (cell_cnt - (cell_cnt % line_cnt)) / line_cnt
        page_width = _width
        page_height = cell_h * cnt
    else:
        page_width = cell_w * cell_cnt
        page_height = cell_h

    if _des == "":
        _des = _folder

    make_fnt(img_list, cell_w, _char_width_offset, cell_h, page_width, page_height, _des, line_cnt)


if __name__ == "__main__":
    main()
