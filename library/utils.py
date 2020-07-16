from typing import Any, List

from django.conf import settings

# fmt: off
LANGUAGES = {"af": "Afrikaans", "sq": "Albanian", "ar": "Arabic", "hy": "Armenian", "az": "Azerbaijani", "eu": "Basque", "be": "Belarusian", "bn": "Bengali", "bs": "Bosnian", "br": "Breton", "bg": "Bulgarian", "my": "Burmese", "ca": "Catalan", "zh": "Chinese", "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch", "en": "English", "eo": "Esperanto", "et": "Estonian", "fi": "Finnish", "fr": "French", "fy": "Frisian", "gd": "Gaelic", "gl": "Galician", "ka": "Georgian", "de": "German", "el": "Greek", "he": "Hebrew", "hi": "Hindi", "hu": "Hungarian", "is": "Icelandic", "io": "Ido", "id": "Indonesian", "ia": "Interlingua", "ga": "Irish", "it": "Italian", "ja": "Japanese", "kn": "Kannada", "kk": "Kazakh", "km": "Khmer", "ko": "Korean", "sr": "Latin", "lv": "Latvian", "lt": "Lithuanian", "lb": "Luxembourgish", "mk": "Macedonian", "ml": "Malayalam", "mr": "Marathi", "mn": "Mongolian", "ne": "Nepali", "nb": "Norwegian", "nn": "Nynorsk", "os": "Ossetic", "fa": "Persian", "pl": "Polish", "pt": "Portuguese", "pa": "Punjabi", "ro": "Romanian", "ru": "Russian", "sk": "Slovak", "sl": "Slovenian", "es": "Spanish", "sw": "Swahili", "sv": "Swedish", "ta": "Tamil", "tt": "Tatar", "te": "Telugu", "th": "Thai", "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu", "uz": "Uzbek", "vi": "Vietnamese", "cy": "Welsh"}.items()  # noqa: B950
# fmt: on


def oxford_comma(items: List[str]) -> str:
    if len(items) > 2:
        items[-1] = "and " + items[-1]
        return ", ".join(items)
    else:
        return " and ".join(items)


def get_hyperlink(item: Any, book: Any = None) -> str:
    return '<a href="{url}">{text}</a>'.format(**(item.get_link_data(book=book)))
