# Copyright 2021 Zuva Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import re
import bs4
from bs4 import BeautifulSoup as bs


def to_bs4(hocr) -> bs4.BeautifulSoup:
    """
    Opens an HOCR file and returns its contents as BeautifulSoup
    """
    with open(hocr) as hocr_document:
        lines = hocr_document.readlines()
        lines = "".join(lines)
        hocr_soup = bs(lines, 'lxml')

    return hocr_soup


def get_confidence(s) -> int:
    """
    Using the input string (for x_wconf), parse out the confidence value and return
    the confidence (100 - confidence)
    """
    conf_rgx = r'''(?<=x_wconf )([0-9]+)'''
    match = re.search(conf_rgx, s.get('title'))
    return 100 - int(match.group(0)) if match else 100


def get_boundingbox(s) -> dict:
    """
    Using the input string (for bbox), parse out the x1, y1, x2, y2 coordinates (i.e. BoundingBox)
    and return a dictionary containing the left/top/right/bottom values.

    The response dictionary defaults the left/top/right/bottom to 0.
    """
    bb_rgx = r'''(?<=bbox )([0-9]{0,4}) ([0-9]{0,4}) ([0-9]{0,4}) ([0-9]{0,4})'''
    bb = {
        "left":0,
        "top":0,
        "right":0,
        "bottom":0
    }

    match = re.search(bb_rgx, s.get('title'))

    if match:
        bb["left"] = int(match.group(1))
        bb["top"] = int(match.group(2))
        bb["right"] = int(match.group(3))
        bb["bottom"] = int(match.group(4))

    return bb


def get_boundingbox_gap(boundingbox: dict, character_count: int) -> int:
    """
    Returns the gap needed for the characters using the right and left positions over a character count.
    """
    return int((boundingbox.get('right') - boundingbox.get('left')) / character_count)


def get_pages(soup) -> bs4.element.ResultSet:
    """
    Returns the soup for the ocr_page
    """
    return soup.find_all("div", {"class":"ocr_page"})


def get_paragraphs(soup) -> bs4.element.ResultSet:
    """
    Returns the soup for the ocr_par
    """
    return soup.find_all("p", {"class":"ocr_par"})


def get_lines(soup) -> bs4.element.ResultSet:
    """
    Returns the soup for the ocr_line
    """
    return soup.find_all("span", {"class":"ocr_line"})


def get_words(soup) -> bs4.element.ResultSet:
    """
    Returns the soup for the ocrx_word
    """
    return soup.find_all("span", {"class":"ocrx_word"})
