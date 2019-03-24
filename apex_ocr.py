import csv
import re
import os
import winsound
from collections import Counter, defaultdict
from datetime import datetime
from pprint import pprint

import cv2
import numpy
import pytesseract
from PIL import ImageGrab

stats_headers = ['Datetime', 'Damage Done', 'Kills', 'Time Survived', 'Respawned Allies', 'Revived Allies',
                 'Killed Champion', 'Squad Placed']
replacements = [('x', ''), ('d', '0'), ('D', '0'), ('o', '0'), ('O', '0'), ('!', '1'), ('l', '1'), ('I', '1'),
                ('}', ')'), ('{', '('), (']', ')'), ('[', '('), ('$', ''), ('\'', ''), ('\"', '')]
tesseract_config = '-c tessedit_char_whitelist=()#01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
headers_matcher_map = {
    'Damage Done': re.compile(r'damagedone.([^\)]+)\)'),
    'Killed Champion': re.compile(r'killedchampion.([^\)]+)\)'),
    'Kills': re.compile(r'kills.([^\)]+)\)'),
    'Respawned Ally': re.compile(r'respawnally.([^\)]+)\)'),
    'Revived Ally': re.compile(r'reviveally.([^\)]+)\)'),
    'Squad Placed': re.compile(r'#([0-9]{1,2})'),
    'Time Survived': re.compile(r'timesurvived.([^\)]+)\)')
}


def process_squad_placed(text_list):
    squad_placed_list = []
    for text in text_list:
        try:
            if int(text[0]) > 1:
                squad_placed_list.append(int(text[0]))
            squad_placed_list.append(int(text))
        except:
            squad_placed_list.append(0)
    return squad_placed_list


def preprocess(img):
    img = img.convert('L')
    img = numpy.array(img)
    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return cv2.resize(img, (0, 0), fx=4, fy=4)


def replace_nondigits(parsed_string):
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
        # if file already exists, just append the game data
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


if __name__ == '__main__':
    # top half of a 1920x1080 screen
    mon = (0, 0, 1920, 1080 / 2)

    print('Watching screen...')
    while True:

        img = preprocess(ImageGrab.grab(bbox=mon))
        text = pytesseract.image_to_string(img, config=tesseract_config)
        text = text.replace("\n", "").replace(" ", "").lower()

        if 'breakdown' in text or 'summary' in text:
            print('[{}] Match Summary Screen Detected. '.format(datetime.now()))
            winsound.Beep(2000, 500)

            # takes 20 duplicate images immediately to get the most common (mode) interpretation later. should take ~2 secs
            dup_images = [ImageGrab.grab(bbox=mon) for _ in range(20)]
            print('[{}] Finished Taking Backup screengrabs. Processing'.format(datetime.now()))
            winsound.Beep(1500, 500)

            mode_interpretation = defaultdict(None)
            mode_interpretation['Datetime'] = datetime.now()
            matches = defaultdict(list)

            for image in dup_images:
                img = preprocess(image)
                text = pytesseract.image_to_string(img, config=tesseract_config)
                text = text.replace("\n", "").replace(" ", "").lower()

                for header, matcher in headers_matcher_map.items():
                    parsed_text = matcher.findall(text)
                    if header == 'Squad Placed':
                        matches[header].extend(process_squad_placed(parsed_text))
                    elif header == 'Time Survived':
                        matches[header].extend(parsed_text)
                    else:
                        matches[header].extend(replace_nondigits(parsed_text))

            for k, v in matches.items():
                counts = Counter(v)
                most_common = counts.most_common(1)
                if len(most_common) > 0:
                    mode_interpretation[k] = most_common[0][0]
                else:
                    mode_interpretation[k] = most_common

            for k, v in mode_interpretation.items():
                if mode_interpretation[k] is None or (
                    isinstance(mode_interpretation[k], list) and len(mode_interpretation[k]) < 1):
                    mode_interpretation[k] = 'Not Captured'

            print('[{}] Finished Processing.'.format(datetime.now()))
            pprint(mode_interpretation)

            # writing to local file
            write_to_file('stats.csv', mode_interpretation)

            print('Watching screen...')
