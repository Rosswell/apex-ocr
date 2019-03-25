# OCR Stat Tracking for Apex Legends

## Requirements
[requirements]: #requirements
* Python >= 3.6
* Apex Legends

## Installation
[installation]: #installation
```
$ git clone git@github.com:Rosswell/apex-stats-ocr.git
$ cd apex-stats-ocr
$ pip install -r requirements.txt --user
```

## Configuration
[configuration]: #configuration

1. Change the name of the csv file to your liking
2. Adjust the `stats_file` variable, if necessary. `stats_file` is the name of the file you'd like to write stats to, 
and must be in the same directory as `apex_ocr.py`. 
3. Adjust the `mon` variable, if necessary. The default value is `1920x1080`. This is a representation of the top half 
of your monitor, because image processing takes less time for smaller images, and the stats on the Match Summary screen 
are on the top half. Thus, the `mon` variable for a `1920x1080` monitor should be `(0, 0, 1920, 1080 / 2)` 
(which is the default value). 

## Usage
[usage]: #usage

**NOTE:** You *must* run Apex Legends in windowed mode for this to work. This is honestly just because I couldn't 
figure out how to capture full screen mode, and Bordered Windowless is good enough.

Simply run
```
$ python apex_ocr.py
```
Which should print `Watching Screen...` to the console, to indicate that the program is actively monitoring screenshots
for the Match Summary screen.

A higher-pitched beep during the Match Summary screen indicates that the Match Summary screen has been recognized. A
subsequent lower-pitched beep indicates that the requisite duplicate images have been taken, and you can now navigate
away from the Match Summary screen. The amount of time between these two beeps should be under 5 seconds (about 2 
during my testing, YMMV). The OCR processing happens subsequently, and successful writing to the stats file is indicated
by a console message.

## Contributing
[contributing]: #contributing

I legit have no idea what I'm going when it comes to OCR, so if you can get a more consistent rate of interpretation of 
the screen, please go ahead and submit a PR. Also just generally I don't anticipate many people using this, so if you 
have any other contributions in mind, do the same, as this is currently very rough.

## License
[license]: #license

Apex-ocr is distributed under the terms of MIT license.

See [LICENSE](LICENSE) for details.