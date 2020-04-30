#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Utility module for screen OCR
#

from PIL import Image, PngImagePlugin
from pytesseract import image_to_string
import tempfile, sys, os

#
# Configuration:
# 1. use languages from extended tessdata (--tessdata-dir)
# 2. treat images as single text line (--psm 7)
# 3. list of used languages (-l)
#
TESSERACT_CONFIG = "--tessdata-dir screens_tesslangs --psm 7 -l eng+rus+chi_sim+ara+jpn+kor"

#
# Image frame areas of useful text
# phone / tablet: different coeffs of areas of different devices
# nick_frames: areas of nicknames frames with delta
# searched_frame: area of text indicating if the screen is from guild search or not (in-game screens are not supported)
#
FRAMES = {
    "phone": {
        "nick_frames": {
            "x0": 410./1334.,
            "y0": 1./3.,
            "dy": 13./75.,
            "w" : 185./1334.,
            "h" : 0.06
        },
        "searched_frame": {
            "x0": 125./1334.,
            "y0": 0,
            "w" : 300./1334.,
            "h" : 55./750.
        }
    },
    "tablet": {
        "nick_frames": {
            "x0": 628./2048.,
            "y0": 0.375,
            "dy": 200./1536.,
            "w" : 284./2048.,
            "h" : 76./1536.,
        },
        "searched_frame": {
            "x0": 200./2048.,
            "y0": 200./1536.,
            "w" : 450./2048.,
            "h" : 75./1536.
        }
    }
}

#
# Aspect ratio of tablet is bout 4:3, while phones have 16:9 or 16:10
#
def is_tablet(size):
    if size[1]/size[0] > 0.65:
        # print("tablet")
        return True
    else:
        # print("phone")
        return False

#
# Crop image with specified area and save with high DPI that Tesseract 'loves'
#
def crop_and_dpi(image, area):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_filename = temp_file.name
    cropped = image.crop(area)
    cropped.save(temp_filename, dpi=(300, 300))
    temp_file.close()
    return temp_filename

#
# Guild search screen detection.
# In-game screens are not supported (yet?)
#
def detect_searched(image):
    size = image.size
    if is_tablet(size):
        pattern = FRAMES["tablet"]["searched_frame"]
    else:
        pattern = FRAMES["phone"]["searched_frame"]
    x0 = pattern["x0"] * size[0]
    y0 = pattern["y0"] * size[1]
    w  = pattern["w"] * size[0]
    h  = pattern["h"] * size[1]
    x1 = x0 + w
    y1 = y0 + h
    area = (x0, y0, x1, y1)
    cropped = crop_and_dpi(image, area)
    with Image.open(cropped) as image:
        text = image_to_string(image, config=TESSERACT_CONFIG)
        image.close()
    os.remove(cropped)
    # print("Detecting searched screen...")
    if text.lower() != u"информация о гильдии": # lower() is needed to preserve ocr text case mistakes
        # print("not a searched screen! text: ", text)
        return False
    # print("searched screen OK")
    return True

#
# Obtain images with nicknames from full screen
#
def process_screen(image):
    cropped_filenames = []
    # if screen is not from guild search - do not process it
    if not detect_searched(image):
        return cropped_filenames
    size = image.size
    if is_tablet(size):
        pattern = FRAMES["tablet"]["nick_frames"]
    else:
        pattern = FRAMES["phone"]["nick_frames"]
    for i in range(0, 4): # 4 players on each screen
        x0 = pattern["x0"] * size[0]
        dy = pattern["dy"] * size[1]
        y0 = pattern["y0"] * size[1] + i*dy
        w  = pattern["w"] * size[0]
        h  = pattern["h"] * size[1]
        x1 = x0 + w
        y1 = y0 + h
        area = (x0, y0, x1, y1)
        cropped = crop_and_dpi(image, area)
        cropped_filenames.append(cropped)
        # cropped images should be removed after processing
    return cropped_filenames

#
# Main OCR function.
# Returns list of processed nicknames on the screen
#
def ocr_core(filename):
    """
    This function will handle the core OCR processing of single image.
    """
    PngImagePlugin.DEBUG = False
    original = Image.open(filename)
    cropped_filenames = process_screen(original)
    original.close()
    # print(cropped_filenames)
    screen = []
    for file in cropped_filenames:
        image = Image.open(file)
        text = image_to_string(image, config=TESSERACT_CONFIG)
        screen.append(text)
        image.close()
        # remove temp cropped file
        os.remove(file)
    return screen

#
# OCR function to process bulk screens (e.g. from folder)
#
def ocr_core_album(filenames):
    """
    This function will handle the core OCR processing of images album.
    """
    guild = []
    for file in filenames:
        screen = ocr_core(file)
        # print(screen)
        guild.append(screen)
    return guild

if __name__ == '__main__':
    path = sys.argv[1]
    if os.path.isfile(path):
        print(ocr_core(path))
    else:
        files = [path + "/" + file for file in sorted(os.listdir(path))]
        # print(files)
        print(ocr_core_album(files))
