import os, argparse, logging
from dearpygui import core, simple
import pyperclip
from converter import Converter
from languages import lang
from translator import MultiTranslator, TRANSLATOR_TYPES, ApiError, AuthenticationError


class Payload:
    def __init__(self):
        """
        A generic payload used to transfer data between callbacks
        This is used so that different elements of the object have predefined type. It allows for more consistant
        null checking.
        """
        self.delete: [str] = []  # list of elements to delete
        self.disable: [str] = []  # list of elements to disable
        self.enable: [str] = []  # list of elements to enable
        self.display_before: str = ''  # when inserting, insert before display_before
        self.file_path: str = ''  # path to a file
        self.file_name: str = ''  # name of a file
        self.parent: str = ''  # parent name
        self.pages: [str] = []  # pages list
        self.text: str = ''  # any kind of text
        self.data_name: str = ''  # a data object
        self.value_name: str = ''  # a value object
        self.destination_value_name: str = ''
        self.source_language_value: str = ''  # source language (for translation)
        self.destination_language_value: str = ''  # source language (for translation)


class Polybiblioglot:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.converter = Converter()
        self.translator: MultiTranslator = MultiTranslator(TRANSLATOR_TYPES.translator)
        self.current_uid = 0
        self.control_window = simple.window("Control", x_pos=0, y_pos=0, height=800)
        self.convert_window_list = []  # todo: this stores windows indefinitely. Figure out a way to delete them.
        self.data_to_save = ''  # this is the data that will be written to the disk by self.save_text
        with self.control_window:
            # allow user to select image to convert
            core.add_text("Select an Image or PDF")
            core.add_button("Select file", callback=lambda *_: core.open_file_dialog(callback=self.select_file))
            language_list = list(lang.keys())
            core.add_text("Default Source Language:")
            core.add_combo(f'default_source_language', label='', items=language_list,
                           default_value='German')
            core.add_text("Default Destiation Language:")
            core.add_combo(f'default_destination_language', label='', items=language_list,
                           default_value='French')

            core.add_text("Translation Method:")
            core.add_combo(f'translation_method', label='',
                           items=list(TRANSLATOR_TYPES.__dict__.values()), default_value=TRANSLATOR_TYPES.translator)

            core.add_text('API token (if using IBM)')
            core.add_input_text(f'api_token', label='', password=True)

    def start(self):
        """
        Starts the app
        :return:
        """
        core.start_dearpygui()

    def _get_uid(self):
        """
        Returns a unique ID that can be used to create unique element names. The ID is only unique to the object
        instance and should not be used outside of the instance itself.
        :return: A array of unique IDs [window title, top copy button id, bottom copy button id]
        """
        uid = self.current_uid
        self.current_uid += 1
        return uid

    def create_convert_window(self, payload: Payload):
        """
        Creates a convert window. This window represents a file. From this window you can convert the file to text.
        Then translate the text. And finally you can save it to a file.
        The window has 3 tabs. The first tab contains all the controls for:
        - converting the file
        - translated the converted file
        - save the text to disk
        - save ethe translation to disk

        :param payload: Payload object
        :return:
        """
        unique_id = self._get_uid()
        window_title = f'{payload.file_name}_{str(unique_id)}'

        convert_window = simple.window(window_title, width=450, height=600,
                                       y_pos=0 + (20 * unique_id), x_pos=200 + (20 * unique_id))
        with convert_window:
            # widget ids
            top_spacer = f'top_{unique_id}'
            bottom_spacer = f'bottom_{unique_id}'

            convert_button = f'convert_{unique_id}'
            translate_button = f'translate_{unique_id}'
            save_text_button = f'save_text_{unique_id}'
            save_translation_button = f'save_translation_{unique_id}'

            text_spacer = f'text_spacer_{unique_id}'
            translated_text_spacer = f'translated_text_spacer_{unique_id}'
            tab_bar_name = f'tab_bar_{unique_id}'
            tab_names = [f'controls_{unique_id}', f'text_{unique_id}', f'translated_{unique_id}']
            tabs = []
            text_value_name = f'text_{unique_id}'  # the name of the value holding the text gathered from OCR
            source_lang_combo_name = f'text_language{unique_id}'
            destination_lang_combo_name = f'destination_language{unique_id}'
            translated_text_value_name = f'translated_text_{unique_id}'  # the name of the value holding the translation
            core.add_value(text_value_name, '')  # the value that stores the OCR text
            core.add_value(translated_text_value_name, '')  # the value that stores the translated text

            # Creating widgets
            tab_bar = simple.tab_bar(tab_bar_name)
            with tab_bar:
                tabs += [simple.tab(tab_names[0], label="Controls")]
                tabs += [simple.tab(tab_names[1], label="Text")]
                tabs += [simple.tab(tab_names[2], label="Translation")]

                # creating the control tab
                with tabs[0]:
                    core.add_text(payload.file_name)
                    core.add_spacing(count=1, name=top_spacer)
                    core.add_spacing(count=1, name=bottom_spacer)

                    language_list = list(lang.keys())
                    core.add_combo(source_lang_combo_name, label='Source Language', items=language_list,
                                   default_value=core.get_value('default_source_language'))
                    core.add_combo(destination_lang_combo_name, label='Destination Language',
                                   items=language_list, default_value=core.get_value('default_destination_language'))
                    # Creating payload for the convert button
                    convert_payload = Payload()
                    convert_payload.value_name = text_value_name
                    convert_payload.file_path = payload.file_path
                    convert_payload.parent = window_title
                    convert_payload.disable = [convert_button]
                    convert_payload.enable = [translate_button, save_text_button]
                    core.add_button(convert_button, label='Convert to Text',
                                    callback=self.convert_file, callback_data=convert_payload)

                    translate_payload = Payload()
                    translate_payload.value_name = text_value_name
                    translate_payload.destination_value_name = translated_text_value_name
                    translate_payload.source_language_value = source_lang_combo_name
                    translate_payload.destination_language_value = destination_lang_combo_name
                    translate_payload.disable = [translate_button]
                    translate_payload.enable = [translate_button, save_translation_button]

                    core.add_button(translate_button, label='Translate Text', enabled=False,
                                    callback=self.translate_text, callback_data=translate_payload)

                    save_text_payload = Payload()
                    save_text_payload.value_name = text_value_name
                    core.add_button(save_text_button, label='Save Text', callback=self.save_prompt,
                                    callback_data=save_text_payload, enabled=False)
                    save_translation_payload = Payload()
                    save_translation_payload.value_name = translated_text_value_name
                    core.add_button(save_translation_button, label='Save Translation',
                                    callback=self.save_prompt, callback_data=save_translation_payload, enabled=False)

                # creating the Text tab
                with tabs[1]:
                    core.add_text('File Text:')
                    core.add_spacing(count=1, name=text_spacer)

                    # this is the text box that holds the text extracted with OCR
                    core.add_text(f'text_box_{unique_id}', source=text_value_name)

                # creating the Translation tab
                with tabs[2]:
                    core.add_text('Translated text:')
                    core.add_spacing(count=1, name=translated_text_spacer)

                    # this is the text box that holds the translated text response
                    core.add_text(f'translated_text_box_{unique_id}', source=translated_text_value_name)

        # add the window to the window list
        self.convert_window_list += [convert_window]

    def save_prompt(self, sender, data: Payload):
        """
        This helper fucntion will set the self.data_to_save attribute using the value passed in data.value_name.
        It will then open a file prompt that will save the data in self.data_to_save to the select file
        :param sender:
        :param data: Payload object
        :return:
        """
        self.data_to_save = core.get_value(data.value_name)
        core.open_file_dialog(callback=self.save_text)

    def save_text(self, sender, data):
        """
        Writes the data in self.data_to_save to the given file path in data.
        :param sender:
        :param data: file path in the format returned by a file prompt
        :return:
        """
        # TODO: warn user about overwriting files
        with open(os.path.join(*data), 'w') as f:
            f.write(self.data_to_save)

    def convert_file(self, sender, data: Payload):
        """
        Callback function, will convert the currently selected image.
        It works asynchronously by calling _convert_file using run_async_function. And once completed, calls
        _convert_file_return_callback to create the text window containing the OCR text gathered from the image.
        :param sender: The sender object (see dearpygui documentation)
        :param data: Payload object
        :return: None
        """
        # if the data has a delete element, delete it
        self._delete_widgets(data.delete)
        self._disable_widgets(data.disable)
        core.run_async_function(self._convert_file, data, return_handler=self._convert_file_return_callback)

    def _convert_file(self, sender, data: Payload):
        """
        The async part of the convert_file function. It does the CPU intensive OCR work and returns the text generated.
        The path to an image can be provided or the image data itself
        :param sender: dearpygui sender object
        :param data: Payload object
        :return: object containing the image path and image text {"image path": image_path, "image text": image_text}
        """
        pages = self.converter.convert_file(path=data.file_path)
        data.pages = pages
        return data

    def _convert_file_return_callback(self, sender, data: Payload):
        """
        The UI synchronous part of the convert_file function. It takes the text generated by the async OCR function and
        displays it in a text window.
        :param sender: dearpygui sender object
        :param data: Payload object
        :return: None
        """
        if not data.pages:
            print("No file selected or file is of the wrong type.")
            return

        full_text = ''
        for page in data.pages:
            full_text = f'{page} - - - - - \n{full_text}'
        core.set_value(data.value_name, full_text)
        self._enable_widgets(data.enable)

    def translate_text(self, sender, data: Payload):
        """
        Will use data.value_name (as a key) to get text in the value storage.
        It will then asynchronously translate the text.
        The source language is defined in the data.source_language attribute
        The destination language is defined in the data.destination_language
        The translated text is stored back into a value storage using data.destination_value_name as a key
        :param sender:
        :param data: Payload object containing the text and source+destination languages
        :return:
        """
        self._disable_widgets(data.disable)

        text = core.get_value(data.value_name)
        data.text = text
        core.run_async_function(self._translate_text, data, return_handler=self._translate_text_callback)
        return data

    def _translate_text(self, sender, data: Payload):
        """
        Asynchronous portion of the translate_text method.
        This is when the API is executed. The results are passed to the callback in the data.text attribute.
        :param sender:
        :param data: Payload object used to pass the translated text.
        :return:
        """
        source_lang = lang[core.get_value(data.source_language_value)]
        destination_lang = lang[core.get_value(data.destination_language_value)]
        try:
            translated_text = self.translator.translate(data.text, source_lang, destination_lang,
                                                    translation_method=core.get_value('translation_method'),
                                                    authentication={'token': core.get_value('api_token')})
        except ApiError as e:
            print(f'{e}')  # TODO: make this logging
            translated_text = f'{e}'

        data.text = translated_text
        return data

    def _translate_text_callback(self, sender, data: Payload):
        """
        The callback portion of the translate_text method.
        Here the translated text is taken from data and put into the value storage with key data.destination_value_name.
        :param sender:
        :param data: Payload object
        :return:
        """
        core.set_value(data.destination_value_name, data.text)
        self._enable_widgets(data.enable)

    def select_file(self, sender, data):
        """
        Sets the selected file path so it can be used later on.
        This sets a global variable containing the path to the currently select image. This image will be converted to
        text by OCR once the user presses the convert image button.
        :param sender: dearpygui sender object
        :param data: data should be the image path object of format ["path/to/directory", "file_name.png"]
        :return: None
        """
        payload = Payload()
        payload.file_path = os.path.join(*data)
        payload.file_name = data[1]
        self.create_convert_window(payload)

    def _disable_widgets(self, widgets: [str]):
        """
        Helper function that takes a list of widget names (ids) and disables them
        :param widgets: list of widget names
        :return:
        """
        if widgets:
            for name in widgets:
                core.configure_item(name, enabled=False)

    def _enable_widgets(self, widgets: [str]):
        """
        Helper function that takes a list of widget names (ids) and enables them
        :param widgets: list of widgets
        :return:
        """
        if widgets:
            for name in widgets:
                core.configure_item(name, enabled=True)

    def _delete_widgets(self, widgets: [str]):
        """
        Helper function that takes a list of widget names (ids) and deletes them
        :param widgets: list of widgets
        :return:
        """
        if widgets:
            for name in widgets:
                core.delete_item(name)


if __name__ == '__main__':
    # Parse the arguments
    parser = argparse.ArgumentParser(
        prog='Polybiblioglot',
        usage='%(prog)s [OPTION}',
        description='A tool used to convert scanned documents to text and translate them.'
    )

    parser.add_argument('-l', '--log-level', action='store', default='INFO', dest='log_level')
    args = parser.parse_args()

    # Initialize the logger
    logger = logging.getLogger(__name__)
    if args.log_level:
        logger.setLevel(args.log_level)

    # Create the console handler
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Create and start PolyBiblioGlot
    pbg = Polybiblioglot(logger=logger)
    pbg.start()
