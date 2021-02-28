# This module is used to translate text from one language to another.
# You can speciify what API should be used

# currently supported API are the free API ins the trannslate module
# IBM cloud free tier

class Translator:
    def __init__(self, type: str):
        if type == 'ibm':
            pass