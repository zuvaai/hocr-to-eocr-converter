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


from recognition_results_pb2 import BoundingBox, Character, Document, CharacterRange, Page
import hashlib
import gzip

# The header to be added to the compiled byte-content of the EOCR file
eocr_header = b'eocr     \n'

# The version of the protobuf schema used
proto_version = 3

# The default page X and Y DPIs (Dots Per Inch)
page_dpi_x = 300
page_dpi_y = 300


def new_document(version: int = proto_version) -> Document:
    """
    Creates a new eOCR Document

    :return: eOCR Document
    """
    return Document(version = version)


def new_character(char, left_x1, top_y1, right_x2, bottom_y2, confidence: int) -> Character:
    """
    Creates a new eOCR Character with bounding boxes and confidence

    :param char: The character to be added
    :param left_x1: The x1 pixel location
    :param top_y1: The y1 pixel location
    :param right_x2: The x2 pixel location
    :param bottom_y2: The y2 pixel location
    :param confidence: The confidence
    :return: EOCR Character
    """
    bb = BoundingBox()
    bb.x1 = left_x1
    bb.y1 = top_y1
    bb.x2 = right_x2
    bb.y2 = bottom_y2

    char = Character(unicode = ord(char),
                     error = confidence,
                     bounding_box = bb)

    return char


def new_page_range(start, end) -> CharacterRange:
    """
    Creates a new eOCR Page CharacterRange

    :param start: The character position of the page's first character
    :param end: The character position of the page's last character
    :return: EOCR CharacterRange
    """
    return CharacterRange(start = start,
                          end = end)


def new_page(range_start, range_end, width, height, dpi_x: int = page_dpi_x, dpi_y: int = page_dpi_y) -> Page:
    """
    Creates a new eOCR Page

    :param start: The character position of the page's first character
    :param end: The character position of the page's last character
    :param width: The page's right (x2) pixel position
    :param height: The page's bottom (y2) pixel position
    :param dpi_x: The page's X DPI
    :param dpi_y: The page's Y DPI
    :return: EOCR Page
    """
    page_range = new_page_range(start = range_start, end = range_end)
    page = Page(range = page_range,
                width = width,
                height = height,
                dpi_x = dpi_x,
                dpi_y = dpi_y)
    return page


def get_eocr_file_content(zuva_document: Document) -> bytes:
    """
    Creates the compiled EOCR content using the eOCR Document.

    :return: The byte-content of the eOCR file
    """
    content = b''
    content += eocr_header
    body = gzip.compress(zuva_document.SerializeToString())
    content += hashlib.sha1(body).digest()
    content += body
    return content
