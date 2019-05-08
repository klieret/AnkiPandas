#!/usr/bin/env python3

import re
from hashlib import sha1
from html.entities import name2codepoint

# Implementation directly copied from Anki (anki/anki/utils.py).
# Only a bit of PEP8ing and making things private.

_reComment = re.compile("(?s)<!--.*?-->")
_reStyle = re.compile("(?si)<style.*?>.*?</style>")
_reScript = re.compile("(?si)<script.*?>.*?</script>")
_reTag = re.compile("(?s)<.*?>")
_reEnts = re.compile(r"&#?\w+;")
_reMedia = re.compile("(?i)<img[^>]+src=[\"']?([^\"'>]+)[\"']?[^>]*>")


def _strip_html(s):
    s = _reComment.sub("", s)
    s = _reStyle.sub("", s)
    s = _reScript.sub("", s)
    s = _reTag.sub("", s)
    s = _ents_to_txt(s)
    return s


def _strip_html_media(s):
    """ Strip HTML but keep media filenames """
    s = _reMedia.sub(" \\1 ", s)
    return _strip_html(s)


def _ents_to_txt(html):
    # entitydefs defines nbsp as \xa0 instead of a standard space, so we
    # replace it first
    html = html.replace("&nbsp;", " ")

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return _reEnts.sub(fixup, html)


def _checksum(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return sha1(data).hexdigest()


def field_checksum(data: str) -> int:
    """ 32 bit unsigned number from first 8 digits of sha1 hash.
    Apply this to the first field to the the field checksum that is used by
    Anki to detect duplicates.

    Args:
        data: string like

    Returns:
        int
    """
    return int(_checksum(_strip_html_media(data).encode("utf-8"))[:8], 16)
