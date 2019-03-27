import csv
import os
import regex
import winsound
from collections import Counter, defaultdict
from datetime import datetime
from pprint import pprint, pformat

import time
import cv2
import numpy
import pytesseract
from PIL import ImageGrab, Image

## CONFIGURABLE VARIABLES
# name of stats file - must be in same dir as this file
stats_file = 'stats.csv'
# top half of a 1920x1080 monitor
mon = (0, 0, 1920, 1080 / 2)

##
stats_headers = ['Datetime', 'Damage Done', 'Kills', 'Time Survived', 'Respawned Allies', 'Revived Allies',
                 'Killed Champion', 'Squad Placed']
replacements = [('x', ''), ('d', '0'), ('D', '0'), ('o', '0'), ('O', '0'), ('!', '1'), ('l', '1'), ('I', '1'),
                ('}', ')'), ('{', '('), (']', ')'), ('[', '('), ('$', ''), ('\'', ''), ('\"', '')]
# This doesn't seem to actually be doing anything, but leaving it in because it's working and I'm scared to change it
tesseract_config = '-c tessedit_char_whitelist=()#01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz --psm 11'
headers_matcher_map = {
    'Damage Done': regex.compile('(?:damagedone\(){e<=2}(.*?)(?:\]|\))'),
    'Killed Champion': regex.compile('(?:killedchampion\(){e<=2}(.*?)(?:\]|\))'),
    'Kills': regex.compile('(?:kills\(){e<=1}(.*?)(?:\]|\))'),
    'Respawned Allies': regex.compile('(?:respawnally\(){e<=2}(.*?)(?:\]|\))'),
    'Revived Allies': regex.compile('(?:reviveally\(){e<=2}(.*?)(?:\]|\))'),
    'Squad Placed': regex.compile('#([0-9]{1,2})'),
    'Time Survived': regex.compile('(?:timesurvived\(){e<=2}(.*?)(?:\]|\))')
}


def process_squad_placed(text_list):
    # for deciphering single-digit squad placement from multi-digit squad placement
    squad_placed_list = []
    for text in text_list:
        try:
            numeric_place = int(text)
            if numeric_place == 2 or numeric_place == 20:
                squad_placed_list.append(20)
            elif  numeric_place == 1 or numeric_place == 10:
                squad_placed_list.append(10)
            elif numeric_place > 20:
                squad_placed_list.append(int(text[0]))
            else:
                squad_placed_list.append(numeric_place)
        except:
            squad_placed_list.append(0)
    return squad_placed_list


def preprocess_image(img):
    img = img.convert('RGB')
    opencv_img = cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2GRAY)
    opencv_thr_img = cv2.threshold(opencv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    opencv_blur_img = cv2.GaussianBlur(opencv_thr_img, (3, 3), 0)
    return opencv_blur_img


def replace_nondigits(parsed_string):
    # making sure the fields that should be numeric are numeric
    return_list = []
    for s in parsed_string:
        for old, new in replacements:
            s = s.replace(old, new)
        try:
            return_list.append(int(s))
        except:
            continue
    return return_list


def write_to_file(filename, data):
    value_list = [data[header] for header in stats_headers]
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.isfile(filepath):
        # if a stats file already exists, just append the game data
        write_method = 'a'
        rows_to_write = [value_list]
    else:
        # if file doesn't exist, create it, write header row, then game data
        write_method = 'w'
        rows_to_write = [stats_headers, value_list]

    with open(filename, write_method, newline='') as f:
        writer = csv.writer(f)
        for row in rows_to_write:
            writer.writerow(row)


def log_and_beep(print_text, beep_freq):
    pprint('[{}] {}'.format(datetime.now(), print_text))
    if beep_freq:
        winsound.Beep(beep_freq, 500)


if __name__ == '__main__':
    print('Watching screen...')
    while True:
        # continuously grab screenshots and interpret them to identify the match summary screen
        img = preprocess_image(ImageGrab.grab(bbox=mon))
        text = pytesseract.image_to_string(img, config=tesseract_config)
        text = text.replace("\n", "").replace(" ", "").lower()

        if 'breakdown' in text or 'summary' in text:
            time.sleep(1)
            log_and_beep('Match Summary screen detected.', 2000)

            # takes 20 duplicate images immediately to get the most common (mode) interpretation later. should take ~2 secs
            dup_images = [ImageGrab.grab(bbox=mon) for _ in range(20)]

            mode_interpretation = defaultdict(None)
            mode_interpretation['Datetime'] = datetime.now()
            matches = defaultdict(list)

            log_and_beep('Finished taking backup screengrabs. Processing images -> text', 1500)
            # OCR for all the images captured, then assign interpretation to the associated stat
            for image in dup_images:
                img = preprocess_image(image)
                text = pytesseract.image_to_string(img, config=tesseract_config)
                text = text.replace("\n", "").replace(" ", "").lower()

                print(text)
                for header, matcher in headers_matcher_map.items():
                    if header == 'Squad Placed':
                        parsed_text = process_squad_placed(matcher.findall(text))
                    elif header == 'Time Survived':
                        parsed_text = matcher.findall(text)
                    else:
                        parsed_text = replace_nondigits(matcher.findall(text))
                    matches[header].extend(parsed_text)

            # for each of the 21 images, find the most common OCR text interpretation for each stat. If there are no
            # available interpretations of the stat, assign the value 'Not Captured' instead
            for k, v in matches.items():
                counts = Counter(v)
                most_common = counts.most_common(1)
                print(k, counts)
                if len(most_common) > 0:
                    mode_interpretation[k] = most_common[0][0]
                else:
                    mode_interpretation[k] = 'Not Captured'

            log_and_beep(
                'Finished processing images. Image interpretations:\n{}'.format(pformat(dict(mode_interpretation))),
                1000)

            # writing to local file
            write_to_file(stats_file, mode_interpretation)
            log_and_beep('Finished writing interpretations to {} file.\nWatching screen...'.format(stats_file), None)
