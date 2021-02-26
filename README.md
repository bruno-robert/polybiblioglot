The official repo URL is https://gitlab.com/brunorobert/polybiblioglot
Although there is a github repository located at https://github.com/bruno-robert/polybiblioglot. All new commits, pull requests, issues should be created on gitlab. 
The github repository is setup to mirror the gitlab repository.

# polybiblioglot

A OCR tool to convert books scans into text and automatically translate them.

# Installation / Setup

## Requirements

### Tesseract

polybiblioglot uses tesseract for OCR, you will need to follow the steps described [here](https://github.com/tesseract-ocr/tesseract#installing-tesseract) to install tesseract.

On macos, you may find [this gist](https://gist.github.com/henrik/1967035) useful.

### Poppler

Poppler is a pdf renderer. In this case, we use it to convert pdf's to images for processing.
If you are only converting images, it isn't needed. Please note that the program may crash if you don't install poppler
and attempt to convert a pdf.

The [pdf2image](https://github.com/Belval/pdf2image) github explains how to install poppler depending on what platform you are on.
If you are on mac and have brew installed. It's as simple as `brew install poppler`

## Installation

Clone the repository:
`git clone https://github.com/bruno-robert/polybiblioglot.git`

cd into it:
`cd polybiblioglot`

(optional) create a python virtual environment:
`python -m venv env`
then
`source ./env/bin/activate`

install python dependancies
`pip install -r requirements.txt`

# Running polybiblioglot

To run polybiblioglot, simply execute the main.py file
`python main.py`

# Notes and limitation (for now)

## Limitations
- Currently, polybiblioglot uses a free API for translation that is limited both in terms of how many calls we can make per day, but also limits each query to 500 chars.
- The OCR method used is optimized for high acuracy and not speed. I might add the functionality to change this in the future.

## Notes

- All computationally expensive or I/O intensive tasks are run asynchronously. This keeps the UI snappy. I'm currently using the DearPyGUI asynchronous call method wich will be depricated in the next version. A migration to python's out of the box threading library will be needed at that point.
