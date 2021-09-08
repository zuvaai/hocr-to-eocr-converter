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

#!/bin/bash
pdfname=$1
dir=$2

filename=$(basename $pdfname)
filename=${filename%.*}
mkdir -p $dir/$filename
magick -density 300 $pdfname -set colorspace RGB -alpha off -resize 2481x3508  $dir/$filename/page-%04d.png
for j in $dir/$filename/*.png
do
  output=$(basename $j)
  output=${output%.*}
  tesseract $j $dir/$filename/$output -l eng hocr
done
rm $dir/$filename/*.png