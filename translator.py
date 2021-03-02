import logging
import requests
import types

from translate import Translator

TRANSLATOR_TYPES = types.SimpleNamespace()
TRANSLATOR_TYPES.translator = 'translator'
TRANSLATOR_TYPES.ibm = 'ibm'

IBM_TRANSLATE_URL = 'https://api.us-south.language-translator.watson.cloud.ibm.com/instances/c9cf4fc5-460c-40fa-8338-b524a9428899/v3/translate?version=2018-05-01'


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
    def __init__(self, translator_type: str, logger: logging.Logger = logging.getLogger(__name__)):
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

    def translate(self, text: str, source: str, destination: str, translation_method='', authentication=None) -> str:
        """
        Translates text using the configured translation API

        :param authentication: The authentication token/username+password/etc. for the translation API. Some
        translation methods will require this or not.
        :param translation_method: (optionallly) defines the API to be
        used. If it's not provided, self.translator_type is used
        :param text: text to translate
        :param source: source language code (eg. 'en')
        :param destination: destination language code (eg. 'de')
        :return: Translated text
        """
        output = ''
        if translation_method == '':
            translation_method = self.translator_type

        if translation_method not in TRANSLATOR_TYPES.__dict__.values():
            self.logger.error('Translation method is invalid')
            raise InvalidTranslationMethod("Translation method is invalid")

        if translation_method == TRANSLATOR_TYPES.translator:
            self.logger.debug('Translating with the translator module')
            translate = Translator(from_lang=source, to_lang=destination)
            output = translate.translate(text[:499])
        elif translation_method == TRANSLATOR_TYPES.ibm:
            self.logger.debug('Translating with IBM')
            try:
                api_token = authentication['token']
            except:
                raise AuthenticationError('The token was not found')
            body = {
                "text": [
                    text
                ],
                "model_id": f'{source}-{destination}'
            }
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request('POST', IBM_TRANSLATE_URL, json=body, auth=('apikey', api_token),
                                        headers=headers)
            if response.status_code != 200:
                raise ApiError(response.text)

            for translation in response.json()['translations']:
                output += translation['translation']
                output += '\n'

        return output
