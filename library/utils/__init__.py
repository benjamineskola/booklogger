import re
from collections.abc import Collection, Iterable, Sequence
from math import floor, log
from typing import Any

from django.http import HttpRequest

from library.models import ApiKey

# fmt: off
LANGUAGES = {"af": "Afrikaans", "sq": "Albanian", "ar": "Arabic", "hy": "Armenian", "az": "Azerbaijani", "eu": "Basque", "be": "Belarusian", "bn": "Bengali", "bs": "Bosnian", "br": "Breton", "bg": "Bulgarian", "my": "Burmese", "ca": "Catalan", "zh": "Chinese", "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch", "en": "English", "eo": "Esperanto", "et": "Estonian", "fi": "Finnish", "fr": "French", "fy": "Frisian", "gd": "Gaelic", "gl": "Galician", "ka": "Georgian", "de": "German", "el": "Greek", "he": "Hebrew", "hi": "Hindi", "hu": "Hungarian", "is": "Icelandic", "io": "Ido", "id": "Indonesian", "ia": "Interlingua", "ga": "Irish", "it": "Italian", "ja": "Japanese", "kn": "Kannada", "kk": "Kazakh", "km": "Khmer", "ko": "Korean", "sr": "Latin", "lv": "Latvian", "lt": "Lithuanian", "lb": "Luxembourgish", "mk": "Macedonian", "ml": "Malayalam", "mr": "Marathi", "mn": "Mongolian", "ne": "Nepali", "nb": "Norwegian", "nn": "Nynorsk", "os": "Ossetic", "fa": "Persian", "pl": "Polish", "pt": "Portuguese", "pa": "Punjabi", "ro": "Romanian", "ru": "Russian", "sk": "Slovak", "sl": "Slovenian", "es": "Spanish", "sw": "Swahili", "sv": "Swedish", "ta": "Tamil", "tt": "Tatar", "te": "Telugu", "th": "Thai", "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu", "uz": "Uzbek", "vi": "Vietnamese", "cy": "Welsh", "yi": "Yiddish"}.items()
# fmt: on


def clean_publisher(publisher: str) -> str:
    messy_re = r" (Books|Limited|Publishing|Publishers|Publications|Ltd\.?|Company|(& *)?Co\.?)*$"
    while re.search(messy_re, publisher):
        publisher = re.sub(messy_re, "", publisher)

    publisher = publisher.strip(" &,")
    publisher = publisher.removeprefix("The ")

    publisher = re.sub("\bUniv. ", "University ", publisher)

    if (
        publisher
        not in [
            "Foreign Languages Press",
            "Free Press",
            "History Press",
            "MIT Press",
            "New Press",
            "Polperro Heritage Press",
        ]
        and "University" not in publisher
    ):
        publisher = publisher.removesuffix(" Press")
    return publisher


def isbn_to_isbn10(isbn: str) -> str:
    if (
        not isbn
        or len(isbn) != 13
        or not isbn.startswith("978")
        or not isbn.isnumeric()
    ):
        return ""

    new_isbn = [int(i) for i in isbn[3:-1]]
    check_digit = 11 - sum((10 - i) * new_isbn[i] for i in range(9)) % 11
    return "".join([str(i) for i in new_isbn]) + (
        "X" if check_digit == 10 else str(check_digit)
    )


def isbn10_to_isbn(isbn: str) -> str:
    if len(isbn) not in [9, 10, 13]:
        return ""
    if len(isbn) == 13:
        return isbn if isbn.isnumeric() else ""
    if not isbn[0:-1].isnumeric():
        return ""
    if not (isbn[-1].isnumeric() or isbn[-1].upper() == "X"):
        return ""

    if len(isbn) == 9:
        # let's assume it's a pre-ISBN SBN
        isbn = f"0{isbn}"

    isbn = f"978{isbn}"
    ints = [int(c) for c in isbn[0:-1]]

    checksum = 0
    for i, j in enumerate(ints):
        if i % 2 == 0:
            checksum += j
        else:
            checksum += j * 3
    checksum = 10 - checksum % 10

    return "".join([str(c) for c in ints] + [str(checksum)])


def oxford_comma(items: Sequence[str]) -> str:
    return (
        ", ".join(items[0:-1]) + ", and " + items[-1]
        if len(items) > 2
        else " and ".join(items)
    )


def round_trunc(number: float, digits: int = 2) -> str:
    if not isinstance(number, float) and not isinstance(number, int):
        return "?" * digits

    num_digits = max(1, int(floor(log(abs(number), 10) + 1))) if number else 1 + digits

    return f"{{:.{num_digits + digits}g}}".format(number)


def str2bool(s: str) -> bool:
    if s.isnumeric():
        return bool(int(s))
    if s.lower() in ["yes", "true", "y", "t"]:
        return True
    if s.lower() in ["no", "false", "n", "f"]:
        return False

    msg = f"Cannot interpret '{s}' as boolean"
    raise ValueError(msg)


def flatten(list_of_lists: Iterable[Iterable[Any] | None]) -> list[Any]:
    return [item for sublist in list_of_lists if sublist for item in sublist]


def remove_stopwords(string: str, stopwords: Collection[str] = ()) -> str:
    if not stopwords:
        stopwords = [
            "a",
            "an",
            "and",
            "at",
            "for",
            "in",
            "is",
            "of",
            "on",
            "the",
            "to",
            "&",
        ]
    return " ".join([word for word in string.split() if word.lower() not in stopwords])


def smarten(string: str) -> str:
    string = re.sub(r"(\w)'(\w)", r"\1’\2", string)
    string = re.sub(r"(\s|^)'(\w)", r"\1‘\2", string)
    string = re.sub(r'(\s|^)"(\w)', r"\1“\2", string)
    string = re.sub(r"(\w)'(\s|$)", r"\1’\2", string)
    string = re.sub(r'(\w)"(\s|$)', r"\1”\2", string)
    string = re.sub(r"(\d)-(\d)", r"\1–\2", string)
    string = re.sub(r" - ", r" — ", string)
    return string


def is_authenticated(request: HttpRequest) -> bool:
    if request.user.is_authenticated:
        return True

    input_key = request.GET.get("key")
    if not input_key:
        return False

    api_keys = ApiKey.objects.filter(key=input_key)
    if api_keys.count():
        return True

    return False
