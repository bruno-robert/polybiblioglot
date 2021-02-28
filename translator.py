import logging
import types
from translate import Translator

TRANSLATOR_TYPES = types.SimpleNamespace()
TRANSLATOR_TYPES.translator = 'translator'
TRANSLATOR_TYPES.ibm = 'ibm'


# This module is used to translate text from one language to another.
# You can speciify what API should be used

# currently supported API are the free API ins the translate module
# IBM cloud free tier

class InvalidTranslationMethod(Exception):
    pass


class AuthenticationError(Exception):
    pass


class ApiError(Exception):
    pass


class MultiTranslator:
    def __init__(self, translator_type: str, logger: logging.Logger = logging.Logger('MultiTranslator')):
        self.logger = logger

        if translator_type in TRANSLATOR_TYPES.__dict__.values():
            self.translator_type = translator_type
        else:
            self.logger.error('Translator API type is not valid.')

    def set_api(self, translator_type: str):
        if translator_type in TRANSLATOR_TYPES.__dict__.values():
            self.translator_type = translator_type
        else:
            self.logger.error('Translator API type is not valid.')

    def translate(self, text: str, source: str, destination: str) -> str:
        """
        Translates text using the configured translation API

        :param text: text to translate
        :param source: source language code (eg. 'en')
        :param destination: destination language code (eg. 'de')
        :return: Translated text
        """
        output = ''

        if self.translator_type == TRANSLATOR_TYPES.translator:
            translate = Translator(from_lang=source, to_lang=destination)
            output = translate.translate(text[:499])
        elif self.translator_type == TRANSLATOR_TYPES.ibm:
            pass

        return output
