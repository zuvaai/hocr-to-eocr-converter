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

# This proof of concept uses the ZDAI Python Wrapper found below:
#   https://github.com/zuvaai/zdai-python
# Comment out lines 22 and 65-onwards if you wish to skip it.


import hashlib
from HOCRToEOCRConverter import HOCRToEOCRConverter
from zdai import ZDAISDK, Language, Classification, Extraction
from datetime import datetime
import time
import os
from colorama import Fore


hocr_folder = 'out/CANADAGOOS-F1Securiti-2152017/'
eocr_file = 'CANADAGOOS-F1Securiti-2152017.eocr'
source_file = 'CANADAGOOS-F1Securiti-2152017.PDF'


def consoleout(msg):
    print(f'[{datetime.now()}] {msg}')


def delete_eocr():
    try:
        os.remove(eocr_file)
        print(f'Deleted {eocr_file}')
    except OSError:
        pass


def get_source_file_md5():
    with open(source_file, 'rb') as source:
        lines = source.read()
        hash = hashlib.md5(lines)
    return hash


delete_eocr()

converter = HOCRToEOCRConverter()
converter.hocr_folder = hocr_folder
md5 = get_source_file_md5()
converter.set_document_md5(md5.digest())

consoleout(f'Starting conversion')
converter.start()
converter.export(eocr_file)
consoleout(f'Conversion done and saved to {eocr_file}')

# Everything below is dependent on the ZDAI Python Wrapper
field_names_to_extract = ['Title', 'Parties', 'Date', 'Governing Law', 'Indemnity']

sdk = ZDAISDK(from_config = True)
fields, _ = sdk.fields.get()
field_ids = [f.id for f in fields if f.name in field_names_to_extract]
consoleout(f'Obtained field_ids for extraction: {", ".join(field_names_to_extract)}')

# Uncomment the below !
with open(eocr_file, 'rb') as eocr:
    file, _ = sdk.file.create(content = eocr.read(), is_eocr = True)
    consoleout(f'Submitted {eocr_file} as {file.id}. It expires on {file.expiration}.')

jobs = []

jobs.extend(sdk.classification.create(file_ids = [file.id])[0])  # Uncomment this!
jobs.extend(sdk.language.create(file_ids = [file.id])[0])  # Uncomment this!
jobs.extend(sdk.extraction.create(file_ids = [file.id], field_ids = field_ids)[0])

for job in jobs:
    consoleout(Fore.BLUE + f'{type(job).__name__}' + Fore.RESET + f' Request ID ' +
               Fore.BLUE + job.request_id + Fore.RESET)
consoleout(f'Waiting for requests to complete')

# Wait for the requests to complete
while len(jobs)>0:
    for job in jobs:
        if isinstance(job, Language):
            _latest, _ = sdk.language.get(request_id = job.request_id)
            if not _latest.is_done(): continue
            if _latest.status == 'failed':
                consoleout(Fore.RED + f'!!! {_latest.request_id} failed !!!' + Fore.RESET)
                consoleout(_latest.json())
                jobs.remove(job)
                continue
            consoleout(Fore.BLUE + f'Language' + Fore.RESET + f'          {_latest.language}')
            jobs.remove(job)

        elif isinstance(job, Classification):
            _latest, _ = sdk.classification.get(request_id = job.request_id)
            if not _latest.is_done(): continue
            if _latest.status == 'failed':
                consoleout(Fore.RED + f'!!! {_latest.request_id} failed !!!' + Fore.RESET)
                consoleout(_latest.json())
                jobs.remove(job)
                continue
            is_contract = 'Yes' if _latest.is_contract else 'No'
            consoleout(Fore.BLUE + f'Classification' + Fore.RESET + f'    {_latest.classification}')
            consoleout(Fore.BLUE + f'Is it a Contract? ' + Fore.RESET + is_contract)
            jobs.remove(job)

        elif isinstance(job, Extraction):
            _latest, _ = sdk.extraction.get(request_id = job.request_id)
            if not _latest.is_done(): continue
            if _latest.status == 'failed':
                consoleout(Fore.RED + f'!!! {_latest.request_id} failed !!!' + Fore.RESET)
                consoleout(_latest.json())
                jobs.remove(job)
                continue
            extraction, _ = sdk.extraction.get_result(request_id = job.request_id)

            for field in extraction.fields:
                if len(field.extractions)>0:
                    field_name = [f.name for f in fields if f.id == field.field_id][0]

                    for field_extraction in field.extractions:
                        # This contains an ExtractionResult: the text & the spans.
                        # We need to use the spans to figure out the bounding boxes from
                        # the list of Zuva Characters (which come from the converter)
                        # Note that the spans property is an array of starts and ends,
                        # So we need to iterate through those to grab their indices.

                        print(f'{field_name}: {field_extraction.text}')

                        for span in field_extraction.spans:
                            zuva_characters = converter.get_eocr_characters_by_range(start = span.get('start'),
                                                                                        end = span.get('end'))

                            # Go through the range of this span to grab the Zuva Characters
                            for i in range(span.get('start'), span.get('end')):
                                zuva_character = converter.zuva_document.characters[i]
                                zuva_page = converter.get_eocr_page_by_character_position(i) + 1  # 0-based indices
                                print(f'   [Field \"{field_name}\"] '
                                      f'[Page: {zuva_page}] '
                                      f'[Character: \"{chr(zuva_character.unicode)}\"] '
                                      f'[BoundingBox: '
                                      f'x1={zuva_character.bounding_box.x1}, '
                                      f'y1={zuva_character.bounding_box.y1}, '
                                      f'x2={zuva_character.bounding_box.x2}, '
                                      f'y2={zuva_character.bounding_box.y2}] '
                                      )

            jobs.remove(job)
    time.sleep(2)