import logging
import os
from dataclasses import dataclass, field
from enum import Enum, unique

from dearpygui import simple
from dearpygui.core import *
from dearpygui.simple import *

from polybiblioglot.components import Converter, MultiTranslator, ApiError, TRANSLATOR_TYPES
from polybiblioglot.lang import lang


@unique
class Panel(Enum):
    """
    This enum stores the names of each of the 3 panels windows
    """
    left = "Left panel"
    center = "Middle panel"
    right = "Right panel"


@dataclass
class Payload:
    """
    A generic payload used to transfer data between callbacks
    This is used so that different elements of the object have predefined type. It allows for more consistant
    null checking.
    """
    delete: [str] = field(default_factory=list)  # list of elements to delete
    disable: [str] = field(default_factory=list)  # list of elements to disable
    enable: [str] = field(default_factory=list)  # list of elements to enable
    display_before: str = field(default='')  # when inserting, insert before display_before
    file_path: str = field(default='')  # path to a file
    file_name: str = field(default='')  # name of a file
    parent: str = field(default='')  # parent name
    pages: [str] = field(default_factory=list)  # pages list
    text: str = field(default='')  # any kind of text
    data_name: str = field(default='')  # a data object
    value_name: str = field(default='')  # a value object
    destination_value_name: str = field(default='')  #
    source_language_value: str = field(default='')  # source language (for translation)
    destination_language_value: str = field(default='')  # source language (for translation)


class Polybiblioglot:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.converter = Converter(logger=logger)
        self.translator: MultiTranslator = MultiTranslator(TRANSLATOR_TYPES.translator, logger=logger)
        self.current_uid = 0
        self.data_to_save = ''  # this is the data that will be written to the disk by self.save_text
        self.__init_main_window()

    @staticmethod
    def _clear_panel(panel: Panel):
        """
        Clears a panel by deleting all it's children.
        :param panel:
        """
        delete_item(panel.value, children_only=True)

    @staticmethod
    def __resize_windows(sender, data):
        """
        This function is called every time the window is resized and when the application starts.
        This function handles the size of the 3 panels that constitute the application.
        The left and right panels are fixed size and the center panel scales as wide and high as possible.

        The sender and data parameters are here because this function is a dearpygui callback.
        :param sender:
        :param data:
        :return:
        """
        width_main_window = get_main_window_size()[0]
        y_pos_panels = get_item_height('Main menu')
        height_panels = get_main_window_size()[1] - 60  # get_item_height('Main') - y_pos_panels
        width_left_panel = 300
        width_right_panel = 400
        width_middle_panel = width_main_window - width_left_panel - width_right_panel
        x_pos_left_panel = 0
        x_pos_middle_panel = x_pos_left_panel + width_left_panel
        x_pos_right_panel = x_pos_middle_panel + width_middle_panel

        # Left panel
        set_window_pos(Panel.left.value, x=x_pos_left_panel, y=y_pos_panels)
        set_item_width(Panel.left.value, width=width_left_panel)
        set_item_height(Panel.left.value, height=height_panels)

        # Middle panel
        set_window_pos(Panel.center.value, x=x_pos_middle_panel, y=y_pos_panels)
        set_item_width(Panel.center.value, width=width_middle_panel)
        set_item_height(Panel.center.value, height=height_panels)

        # Right panel
        set_window_pos(Panel.right.value, x=x_pos_right_panel, y=y_pos_panels)
        set_item_width(Panel.right.value, width=width_right_panel)
        set_item_height(Panel.right.value, height=height_panels)

    def __init_main_window(self):
        with window("Main"):
            # Create the menu
            with menu_bar('Main menu'):
                with menu('File'):
                    add_menu_item('Settings')
                    add_menu_item('Save original text')
                    add_menu_item('Save translated text')
                with menu('Edit'):
                    add_menu_item('Item 1##Edit')
                with menu('Help'):
                    add_menu_item('About PolyBiblioGlot')

        with window(Panel.left.value, autosize=False, no_resize=True, no_title_bar=True, no_move=True,
                    no_scrollbar=True,
                    no_collapse=True, horizontal_scrollbar=False, no_focus_on_appearing=True,
                    no_bring_to_front_on_focus=False,
                    no_close=True, no_background=False, show=True):
            add_text("Select an Image or PDF")
            add_button("Select file", callback=lambda *_: open_file_dialog(callback=self.select_file))
            language_list = list(lang.keys())
            add_text("Default Source Language:")
            add_combo(f'default_source_language', label='', items=language_list,
                      default_value='German')
            add_text("Default Destiation Language:")
            add_combo(f'default_destination_language', label='', items=language_list,
                      default_value='French')

            add_text("Translation Method:")
            add_combo(f'translation_method', label='',
                      items=list(TRANSLATOR_TYPES.__dict__.values()), default_value=TRANSLATOR_TYPES.translator)

            add_text('API token (if using IBM)')
            add_input_text(f'api_token', label='', password=True)

        with window(Panel.center.value, autosize=False, no_resize=True, no_title_bar=True, no_move=True,
                    no_scrollbar=True,
                    no_collapse=True, horizontal_scrollbar=False, no_focus_on_appearing=True,
                    no_bring_to_front_on_focus=False,
                    no_close=True, no_background=False, show=True):
            add_text(Panel.center.value)

        with window(Panel.right.value, autosize=False, no_resize=True, no_title_bar=True, no_move=True,
                    no_scrollbar=True,
                    no_collapse=True, horizontal_scrollbar=False, no_focus_on_appearing=True,
                    no_bring_to_front_on_focus=False,
                    no_close=True, no_background=False,
                    show=True):  # no_background=False --> set to True to remove lines around window
            add_text(Panel.right.value)

        set_start_callback(self.__resize_windows)
        set_resize_callback(self.__resize_windows)

    def start(self):
        """
        Starts the app
        :return:
        """
        start_dearpygui(primary_window="Main")

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

        convert_window = window(window_title, width=450, height=600,
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
            add_value(text_value_name, '')  # the value that stores the OCR text
            add_value(translated_text_value_name, '')  # the value that stores the translated text

            # Creating widgets
            tab_bar = simple.tab_bar(name=tab_bar_name)
            with tab_bar:
                tabs += [tab(tab_names[0], label="Controls")]
                tabs += [tab(tab_names[1], label="Text")]
                tabs += [tab(tab_names[2], label="Translation")]

                # creating the control tab
                with tabs[0]:
                    add_text(payload.file_name)
                    add_spacing(count=1, name=top_spacer)
                    add_spacing(count=1, name=bottom_spacer)

                    language_list = list(lang.keys())
                    add_combo(source_lang_combo_name, label='Source Language', items=language_list,
                              default_value=get_value('default_source_language'))
                    add_combo(destination_lang_combo_name, label='Destination Language',
                              items=language_list, default_value=get_value('default_destination_language'))
                    # Creating payload for the convert button
                    convert_payload = Payload()
                    convert_payload.value_name = text_value_name
                    convert_payload.file_path = payload.file_path
                    convert_payload.parent = window_title
                    convert_payload.disable = [convert_button]
                    convert_payload.enable = [translate_button, save_text_button]
                    add_button(convert_button, label='Convert to Text',
                               callback=self.convert_file, callback_data=convert_payload)

                    translate_payload = Payload()
                    translate_payload.value_name = text_value_name
                    translate_payload.destination_value_name = translated_text_value_name
                    translate_payload.source_language_value = source_lang_combo_name
                    translate_payload.destination_language_value = destination_lang_combo_name
                    translate_payload.disable = [translate_button]
                    translate_payload.enable = [translate_button, save_translation_button]

                    add_button(translate_button, label='Translate Text', enabled=False,
                               callback=self.translate_text, callback_data=translate_payload)

                    save_text_payload = Payload()
                    save_text_payload.value_name = text_value_name
                    add_button(save_text_button, label='Save Text', callback=self.save_prompt,
                               callback_data=save_text_payload, enabled=False)
                    save_translation_payload = Payload()
                    save_translation_payload.value_name = translated_text_value_name
                    add_button(save_translation_button, label='Save Translation',
                               callback=self.save_prompt, callback_data=save_translation_payload, enabled=False)

                # creating the Text tab
                with tabs[1]:
                    add_text('File Text:')
                    add_spacing(count=1, name=text_spacer)

                    # this is the text box that holds the text extracted with OCR
                    add_text(f'text_box_{unique_id}', source=text_value_name)

                # creating the Translation tab
                with tabs[2]:
                    add_text('Translated text:')
                    add_spacing(count=1, name=translated_text_spacer)

                    # this is the text box that holds the translated text response
                    add_text(f'translated_text_box_{unique_id}', source=translated_text_value_name)

        # add the window to the window list
        self.convert_window_list += [convert_window]

    def update_convert_pane(self, payload: Payload):
        """
        Updates the converter panel. This window represents a file. From this window you can convert the file to text.
        Then translate the text. And finally you can save it to a file.
        The window has 3 tabs. The first tab contains all the controls for:
        - converting the file
        - translated the converted file
        - save the text to disk
        - save ethe translation to disk

        :param payload: Payload object
        :return:
        """
        self._clear_panel(Panel.center)
        unique_id = self._get_uid()
        window_title = f'{payload.file_name}_{str(unique_id)}'

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
        add_value(text_value_name, '')  # the value that stores the OCR text
        add_value(translated_text_value_name, '')  # the value that stores the translated text

        # Creating widgets
        tab_bar = simple.tab_bar(name=tab_bar_name, parent=Panel.center.value)
        with tab_bar:
            tabs += [tab(tab_names[0], label="Controls")]
            tabs += [tab(tab_names[1], label="Text")]
            tabs += [tab(tab_names[2], label="Translation")]

            # creating the control tab
            with tabs[0]:
                add_text(payload.file_name)
                add_spacing(count=1, name=top_spacer)
                add_spacing(count=1, name=bottom_spacer)

                language_list = list(lang.keys())
                add_combo(source_lang_combo_name, label='Source Language', items=language_list,
                          default_value=get_value('default_source_language'))
                add_combo(destination_lang_combo_name, label='Destination Language',
                          items=language_list, default_value=get_value('default_destination_language'))
                # Creating payload for the convert button
                convert_payload = Payload()
                convert_payload.value_name = text_value_name
                convert_payload.file_path = payload.file_path
                convert_payload.parent = window_title
                convert_payload.disable = [convert_button]
                convert_payload.enable = [translate_button, save_text_button]
                add_button(convert_button, label='Convert to Text',
                           callback=self.convert_file, callback_data=convert_payload)

                translate_payload = Payload()
                translate_payload.value_name = text_value_name
                translate_payload.destination_value_name = translated_text_value_name
                translate_payload.source_language_value = source_lang_combo_name
                translate_payload.destination_language_value = destination_lang_combo_name
                translate_payload.disable = [translate_button]
                translate_payload.enable = [translate_button, save_translation_button]

                add_button(translate_button, label='Translate Text', enabled=False,
                           callback=self.translate_text, callback_data=translate_payload)

                save_text_payload = Payload()
                save_text_payload.value_name = text_value_name
                add_button(save_text_button, label='Save Text', callback=self.save_prompt,
                           callback_data=save_text_payload, enabled=False)
                save_translation_payload = Payload()
                save_translation_payload.value_name = translated_text_value_name
                add_button(save_translation_button, label='Save Translation',
                           callback=self.save_prompt, callback_data=save_translation_payload, enabled=False)

            # creating the Text tab
            with tabs[1]:
                add_text('File Text:')
                add_spacing(count=1, name=text_spacer)

                # this is the text box that holds the text extracted with OCR
                add_text(f'text_box_{unique_id}', source=text_value_name)

            # creating the Translation tab
            with tabs[2]:
                add_text('Translated text:')
                add_spacing(count=1, name=translated_text_spacer)

                # this is the text box that holds the translated text response
                add_text(f'translated_text_box_{unique_id}', source=translated_text_value_name)

        # add the window to the window list

    def save_prompt(self, sender, data: Payload):
        """
        This helper fucntion will set the self.data_to_save attribute using the value passed in data.value_name.
        It will then open a file prompt that will save the data in self.data_to_save to the select file
        :param sender:
        :param data: Payload object
        :return:
        """
        self.data_to_save = get_value(data.value_name)
        open_file_dialog(callback=self.save_text)

    def save_text(self, sender, data):
        """
        Writes the data in self.data_to_save to the given file path in data.
        :param sender:
        :param data: file path in the format returned by a file prompt
        :return:
        """
        # TODO: prompt user about overwriting files
        with open(os.path.join(*data), 'w') as f:
            f.write(self.data_to_save)

    def convert_file(self, sender, data: Payload):
        """
        Callback function, will convert the currently selected image into text.
        :param sender: The sender object (see dearpygui documentation)
        :param data: Payload object
        :return: None
        """
        # if the data has a delete element, delete it
        self._delete_widgets(data.delete)
        self._disable_widgets(data.disable)
        pages = self.converter.convert_file(path=data.file_path)
        if not pages:
            self.logger.error("No file selected or file is of the wrong type.")
            return

        full_text = ''
        for page in pages:
            full_text = f'{page} - - - - - \n{full_text}'
        set_value(data.value_name, full_text)
        self._enable_widgets(data.enable)

    def translate_text(self, sender, data: Payload):
        """
        Will use data.value_name (as a key) to get text in the value storage.
        The source language is defined in the data.source_language attribute
        The destination language is defined in the data.destination_language
        The translated text is stored back into a value storage using data.destination_value_name as a key
        :param sender:
        :param data: Payload object containing the text and source+destination languages
        :return:
        """
        self._disable_widgets(data.disable)

        text = get_value(data.value_name)
        source_lang = lang[get_value(data.source_language_value)]
        destination_lang = lang[get_value(data.destination_language_value)]
        try:
            translated_text = self.translator.translate(text, source_lang, destination_lang,
                                                        translation_method=get_value('translation_method'),
                                                        authentication={'token': get_value('api_token')})
        except ApiError as e:
            self.logger.error(f'API error: {e}')
            translated_text = f'{e}'

        set_value(data.destination_value_name, translated_text)
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
        self.update_convert_pane(payload)

    def _disable_widgets(self, widgets: [str]):
        """
        Helper function that takes a list of widget names (ids) and disables them
        :param widgets: list of widget names
        :return:
        """
        if widgets:
            for name in widgets:
                configure_item(name, enabled=False)

    def _enable_widgets(self, widgets: [str]):
        """
        Helper function that takes a list of widget names (ids) and enables them
        :param widgets: list of widgets
        :return:
        """
        if widgets:
            for name in widgets:
                configure_item(name, enabled=True)

    def _delete_widgets(self, widgets: [str]):
        """
        Helper function that takes a list of widget names (ids) and deletes them
        :param widgets: list of widgets
        :return:
        """
        if widgets:
            for name in widgets:
                delete_item(name)
