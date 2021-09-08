# HOCR to ZuvaOCR Converter

This proof of concept converts `.hocr` to `.zuvaocr`.  
Note that this converter only supports the words (ocrx_word), lines (ocr_line), paragraphs (ocr_par) and pages (
ocr_page) from the `.hocr` content.

# The ZuvaOCR File Format

A `.zuvaocr` is a format that Zuva Document AI recognizes as "pre-OCR'd" content - in other words, Zuva Document AI will
not run the document through the OCR engine if a `.zuvaocr` is provided.

There are two main components of a `.zuvaocr` file:

1. The header;
2. The body (i.e. an instance of the `Document` message from `recognition_results_pb2.proto`)

In order, the `.zuvaocr` contains the above components:

1. The header;
2. The sha1 digest of the body
3. The body, g-zip compressed

# Using recognition_results_pb2.proto

This `.proto` contains the Protobuf messages. These messages can be used to create instance objects in your programming
language of choice (for example, an instance of a ZuvaOCR `Character`)  
To do this, you will need to use the `protoc` command compile the `.proto` for your programming language.

The following can be used to create the Python classes which represent the `.proto` file, since this proof of concept
was written in Python:

`protoc -I=. --python_out=. recognition_results.proto`

Additional information about Protobuf can be found in the following
link: https://developers.google.com/protocol-buffers/docs/pythontutorial#compiling-your-protocol-buffers

For convenience, a copy of `recognition_results_pb2.py` is provided in this repository.

# Usage

The following is an example of how to use the `HOCRToZuvaOCRConverter` class:

```python
from HOCRToZuvaOCRConverter import HOCRToZuvaOCRConverter

converter = HOCRToZuvaOCRConverter()
converter.hocr_folder = ''  # The folder that contains the list of .hocr for each page OCR'd out of the source file
converter.set_document_md5(b'')  # The source file's md5 .digest()
converter.start()
converter.export('')  # The file path (including file name) of the resultant .zuvaocr
```

This script can be used in conjunction with
the [Zuva Document AI Python Wrapper](https://github.com/zuvaai/zdai-python) sample code,  
where you can take resultant `.zuvaocr` content and submit it to Zuva via `file.create`.

# Licensing

The code is licensed under the Apache License, Version 2.0. See LICENSE for the full license text.