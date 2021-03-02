from pdf2image import convert_from_path
import pytesseract
import logging
from PIL import Image


class Converter:
    def __init__(self, logger=logging.getLogger(__name__)):
        """
        Converter objects are used to convert images or pdf to text.
        """
        self.logger = logger
        pass

    @staticmethod
    def convert_image(image_path="", image_data=None):
        """
        Converts an image to text and returns the text gathered from an image.
        the function can either be provided a path to the image or the image data/object itself.
        It will return the text extracted from the image.
        When nothing is provided, it returns an empty string. Eh!

        :param image_path: image path
        :param image_data: image data object
        :return: string containing text extracted from the image
        """
        if image_data is not None:
            return pytesseract.image_to_string(image_data)
        elif image_path != "" and image_path is not None:
            return pytesseract.image_to_string(Image.open(image_path))
        else:
            return ""

    def convert_images(self, image_list) -> [str]:
        """
        Converts a list of image objects to text using OCR.
        Returns a list of strings containing the text from the images in the same orders
        as the images were passed in

        :param image_list: list of image objects
        :return: list of strings
        """
        text_list = []
        for image in image_list:
            text = self.convert_image(image_data=image)
            text_list += [text]
        return text_list

    def convert_pdf(self, pdf_path) -> [str]:
        """
        Converts a pdf to text. The output is an array of text with each page of the pdf being an element of the
        array

        :param pdf_path: path to the pdf
        :return: array of text (1 page in pdf = 1 element)
        """

        # convert the pdf to and array of images
        images = convert_from_path(pdf_path, fmt='jpeg')
        pdf_pages_txt = self.convert_images(images)
        return pdf_pages_txt

    def convert_file(self, path) -> [str]:
        """
        Converts a file to text and returns the text in an array.
        If the file is an image, the array will be of length 1.
        If the file is a pdf, the array will be the same length as the number of pages (1 element per page)

        :param path: path to the file to convert
        :return: array containing text extracted from image or pdf
        """
        if path is None:
            self.logger.error('Conversion aborted. No path provided.')
            return []
        if path.lower().endswith('.pdf'):
            return self.convert_pdf(pdf_path=path)
        elif path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return [self.convert_image(image_path=path)]
        else:
            self.logger.error('Conversion aborted. File type unsupported.')

    def get_text_from_dir(self, path):
        """
        Converts all images in a folder to text.
        :param path:
        :return:
        """
        pass
