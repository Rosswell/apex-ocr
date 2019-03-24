import csv
import re
import winsound
from collections import Counter, defaultdict
from datetime import datetime
from pprint import pprint

import cv2
import numpy
import pytesseract
from PIL import ImageGrab

cols = ['Damage Done', 'Datetime', 'Killed Champion', 'Kills', 'Respawned Ally', 'Revived Ally', 'Squad Placed',
        'Time Survived']
replacements = [('x', ''), ('d', '0'), ('D', '0'), ('o', '0'), ('O', '0'), ('!', '1'), ('l', '1'), ('I', '1'),
                ('}', ')'), ('{', '('), (']', ')'), ('[', '('), ('$', ''), ('\'', ''), ('\"', '')]
tesseract_config = '-c tessedit_char_whitelist=()#01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
timesurvived_matcher = re.compile(r'timesurvived.([^\)]+)\)')
kills_matcher = re.compile(r'kills.([^\)]+)\)')
killedchampion_matcher = re.compile(r'killedchampion.([^\)]+)\)')
damagedone_matcher = re.compile(r'damagedone.([^\)]+)\)')
reviveally_matcher = re.compile(r'reviveally.([^\)]+)\)')
respawnally_matcher = re.compile(r'respawnally.([^\)]+)\)')
squadplaced_matcher = re.compile(r'#([0-9]{1,2})')


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

                matches['Time Survived'].extend(timesurvived_matcher.findall(text))
                matches['Kills'].extend(replace_nondigits(kills_matcher.findall(text)))
                matches['Killed Champion'].extend(replace_nondigits(killedchampion_matcher.findall(text)))
                matches['Damage Done'].extend(replace_nondigits(damagedone_matcher.findall(text)))
                matches['Revived Ally'].extend(replace_nondigits(reviveally_matcher.findall(text)))
                matches['Respawned Ally'].extend(replace_nondigits(respawnally_matcher.findall(text)))
                matches['Squad Placed'].extend(process_squad_placed(squadplaced_matcher.findall(text)))

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
            with open('stats.csv', "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([mode_interpretation[col] for col in cols])

            print('Watching screen...')
