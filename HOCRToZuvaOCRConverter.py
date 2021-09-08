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
from os import listdir
from os.path import isfile, join

import zuvaocr_helper
import hocr_helper
from datetime import datetime


class HOCRToZuvaOCRConverter(object):
    def __init__(self):
        self.zuva_document = zuvaocr_helper.new_document()
        self.hocr_folder = None

    def consoleout(self, msg):
        """
        Writes to console with a datetime prepended.

        :param msg: The string to print on the console.
        """
        print(f'[{datetime.now()}] {msg}')

    def get_hocr_files(self):
        """
        Gets all of the files in the hocr_folder that end with .hocr.
        """
        hocr_files = [f for f in listdir(self.hocr_folder)
                      if isfile(join(self.hocr_folder, f))
                      and f.endswith('.hocr')]

        hocr_files.sort(key = lambda f:int(re.sub('\D', '', f)))

        return hocr_files

    def set_document_md5(self, md5):
        """
        Function to set the converter's source file md5 value

        :param md5: The message digest of the source file (that was used to generate the .hocr).

        """
        self.zuva_document.md5 = md5

    def add_document_characters(self, chars):
        """
        Adds the characters list to the converted output.

        :param chars: An array of Zuva OCR characters
        """
        self.zuva_document.characters.extend(chars)

    def add_document_page(self, range_start, page):
        """
        Adds a new page to the Zuva OCR document

        :param range_start: The character index of where the page starts
        :param page: The page boundingbox
        """
        page_bbox = hocr_helper.get_boundingbox(page)

        new_page = zuvaocr_helper.new_page(range_start = range_start,
                                           range_end = len(self.zuva_document.characters),
                                           width = page_bbox.get('right'),
                                           height = page_bbox.get('bottom'))

        self.zuva_document.pages.append(new_page)

    def _add_character_space(self, current_bbox, next_bbox):
        """
        Adds a new Zuva OCR character (space) on the same line as the previous character.

        :param current_bbox: The current boundingbox of the hocr word that was parsed.
        :param next_bbox: The next boundingbox of the hocr word that was just parsed.
        """
        char = zuvaocr_helper.new_character(char = " ",
                                            left_x1 = current_bbox.get('right'),
                                            top_y1 = current_bbox.get('top'),
                                            right_x2 = next_bbox.get('left'),
                                            bottom_y2 = current_bbox.get('bottom'),
                                            confidence = 0)
        self.add_document_characters([char])

    def _add_line_space(self, bbox):
        """
        Adds a new line using the current character's boundingbox. This is used for when the hocr word
        that was just converted was the last word on the line.

        :param bbox: The current boundingbox of the hocr word that was parsed.
        """
        char = zuvaocr_helper.new_character(char = " ",
                                            left_x1 = bbox.get('right'),
                                            top_y1 = bbox.get('top'),
                                            right_x2 = bbox.get('right'),
                                            bottom_y2 = bbox.get('bottom'),
                                            confidence = 0)
        self.add_document_characters([char])

    def _add_paragraph_space(self, bbox):
        """
        Adds a new paragraph line using the current character's boundingbox.
        The Zuva OCR character boundingbox values are set the same way as a line space. This
        function exists to make it easier to follow the flow in the self.start()

        :param bbox: The current boundingbox of the hocr word that was parsed.
        """
        self._add_line_space(bbox)

    def _load_hocr_word_as_zuva_characters(self, hocr_word):
        """
        Loads the hocr-word as Zuva OCR characters.

        :param hocr_word: The hocr "ocrx_word" entry
        :return: Does not return anything. This loads the Zuva OCR characters array in the final results.
        """
        zuva_chars = []
        chars = list(hocr_word.text)
        confidence = hocr_helper.get_confidence(hocr_word)
        bbox = hocr_helper.get_boundingbox(hocr_word)
        gap = hocr_helper.get_boundingbox_gap(bbox, len(chars))
        left = bbox.get('left')
        top = bbox.get('top')
        bottom = bbox.get('bottom')

        for i, c in enumerate(chars):
            if left + gap>bbox.get('right'):
                right = bbox.get('right')
            else:
                right = left + gap

            if i == len(chars) - 1:
                right = bbox.get('right')

            new_character = zuvaocr_helper.new_character(char = c,
                                                         left_x1 = left,
                                                         top_y1 = top,
                                                         right_x2 = right,
                                                         bottom_y2 = bottom,
                                                         confidence = confidence)

            zuva_chars.append(new_character)
            left = right

        self.add_document_characters(zuva_chars)

    def start(self):
        if self.hocr_folder is None:
            raise Exception(f'hocr_folder is not set.')

        if not self.zuva_document.md5:
            raise Exception(f'source_hash must be provided (use set_document_md5())')

        for hocr_filename in self.get_hocr_files():
            hocr = join(self.hocr_folder, hocr_filename)

            soup = hocr_helper.to_bs4(hocr)

            for page in hocr_helper.get_pages(soup):
                start = len(self.zuva_document.characters)

                for paragraph in hocr_helper.get_paragraphs(page):
                    for line in hocr_helper.get_lines(paragraph):
                        words = hocr_helper.get_words(line)

                        for i, word in enumerate(words):
                            self._load_hocr_word_as_zuva_characters(word)

                            # If this isn't the last word in the line, add a space after it.
                            if i != len(words) - 1:
                                next_bbox = hocr_helper.get_boundingbox(words[i + 1])
                                current_bbox = hocr_helper.get_boundingbox(word)
                                self._add_character_space(current_bbox, next_bbox)

                        line_bbox = hocr_helper.get_boundingbox(line)
                        self._add_line_space(line_bbox)

                    paragraph_bbox = hocr_helper.get_boundingbox(paragraph)
                    self._add_paragraph_space(paragraph_bbox)

                self.add_document_page(start, page)

                self.consoleout(f'{hocr_filename} converted! (ZuvaOCR now contains {len(self.zuva_document.pages)} '
                                f'page(s) and {len(self.zuva_document.characters)} character(s))')

    def export(self, output_file):
        content = zuvaocr_helper.get_zuvaocr_file_content(self.zuva_document)

        with open(output_file, "wb") as output:
            output.write(content)

    def get_zuvaocr_characters_by_range(self, start, end):
        return [c for c in self.zuva_document.characters[start:end]]

    def get_zuvaocr_pages_by_character_range(self, start, end):
        _page_start = None
        _page_end = _page_start

        for pg_number, page in enumerate(self.zuva_document.pages, 1):
            if page.range.start<=start<=page.range.end:
                _page_start = pg_number

            if page.range.start<=end<=page.range.end:
                _page_end = pg_number

        return {'start':_page_start, 'end':_page_end}

    def get_zuvaocr_page_by_character_position(self, position):
        _pg_number = None

        for pg_number, page in enumerate(self.zuva_document.pages, 0):
            if page.range.start<=position<=page.range.end:
                _pg_number = pg_number
                return _pg_number

        raise Exception(f'Could not find a page with character position {position}')
