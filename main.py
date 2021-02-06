import os
from dearpygui import core, simple
import pyperclip
from converter import Converter


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
        self.language: str = ''  # a language


class Polybiblioglot:
    def __init__(self):
        self.converter = Converter()
        self.current_uid = 0
        self.control_window = simple.window("Control", x_pos=0, y_pos=0, height=800)
        self.convert_window_list = []  # todo: this stores windows indefinitely. Figure out a way to delete them.
        with self.control_window:
            # allow user to select image to convert
            core.add_text("Select an Image or PDF")
            core.add_button("Select file", callback=lambda *_: core.open_file_dialog(callback=self.select_file))

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

    def create_text_window(self, payload: Payload):
        """
        Creates a text window. It's simply a window with some text. There are two copy to clipboard buttons. One above
        and one bellow the text.
        Use this to create a window containing a lot of text.
        :param payload: Payload object
        :return: None
        """
        unique_id = self._get_uid()
        unique_ids = [
            f"{payload.file_name}_{str(unique_id)}",
            f"top_copy_btn_{str(unique_id)}",
            f"bottom_copy_btn_{str(unique_id)}"
        ]
        with simple.window(unique_ids[0]):
            core.add_button(unique_ids[1], label="Copy to clipboard",
                            callback=lambda source, data: pyperclip.copy(data),
                            callback_data=payload.text)
            core.add_text(payload.text)
            core.add_button(unique_ids[2], label="Copy to clipboard",
                            callback=lambda source, data: pyperclip.copy(data),
                            callback_data=payload.text)

    def create_convert_window(self, payload: Payload):
        """
        Creates a convert window. This window represents a file. From this window you can convert the file to text.
        Then translate the text. And finally you can save it to a file.
        :param payload: Payload object
        :return:
        """
        unique_id = self._get_uid()
        window_title = f'{payload.file_name}_{str(unique_id)}'

        convert_window = simple.window(window_title)
        with convert_window:
            # widget ids
            top_spacer = f'top_{unique_id}'
            bottom_spacer = f'bottom_{unique_id}'
            convert_button = f'convert_{unique_id}'
            translate_button = f'translate_{unique_id}'
            text_spacer = f'text_spacer_{unique_id}'
            translated_text_spacer = f'translated_text_spacer_{unique_id}'
            tab_bar_name = f'tab_bar_{unique_id}'
            tab_names = [f'controls_{unique_id}', f'text_{unique_id}', f'translated_{unique_id}']
            tabs = []

            # Creating widgets
            tab_bar = simple.tab_bar(tab_bar_name)
            with tab_bar:
                tabs += [simple.tab(tab_names[0], label="Controls")]
                tabs += [simple.tab(tab_names[1], label="Text")]
                tabs += [simple.tab(tab_names[2], label="Translation")]

                with tabs[0]:
                    core.add_text(payload.file_name)
                    core.add_spacing(count=1, name=top_spacer)
                    core.add_spacing(count=1, name=bottom_spacer)

                    # Creating payload for the convert button
                    convert_payload = Payload()
                    convert_payload.display_before = text_spacer
                    convert_payload.file_path = payload.file_path
                    convert_payload.parent = window_title
                    convert_payload.disable = [convert_button]
                    convert_payload.enable = [translate_button]
                    core.add_button(convert_button, label='Convert to Text',
                                    callback=self.convert_file, callback_data=convert_payload)

                    translate_payload = Payload()
                    core.add_button(translate_button, label='Translate Text', enabled=False,
                                    callback=self.translate_text, callback_data=translate_payload)
                with tabs[1]:
                    core.add_text('File Text:')
                    core.add_spacing(count=1, name=text_spacer)

                with tabs[2]:
                    core.add_text('Translated text:')
                    core.add_spacing(count=1, name=translated_text_spacer)


        # add the window to the window list
        self.convert_window_list += [convert_window]

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
        if data.delete:
            for name in data.delete:
                core.delete_item(name)
        if data.disable:
            for name in data.disable:
                core.configure_item(name, enabled=False)
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
        for page in data.pages:
            core.add_text(page, parent=data.parent, before=data.display_before)
        if data.enable:
            for name in data.enable:
                core.configure_item(name, enabled=True)

    def translate_text(self, sender, data: Payload):
        pass

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


if __name__ == '__main__':
    pbg = Polybiblioglot()
    pbg.start()
