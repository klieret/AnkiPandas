#!/usr/bin/env python3

import re
from hashlib import sha1
from html.entities import name2codepoint

""" Directly copied from Anki: anki/anki/utils.py
Only a bit of PEP8ing"""

reComment = re.compile("(?s)<!--.*?-->")
reStyle = re.compile("(?si)<style.*?>.*?</style>")
reScript = re.compile("(?si)<script.*?>.*?</script>")
reTag = re.compile("(?s)<.*?>")
reEnts = re.compile(r"&#?\w+;")
reMedia = re.compile("(?i)<img[^>]+src=[\"']?([^\"'>]+)[\"']?[^>]*>")


def strip_html(s):
    s = reComment.sub("", s)
    s = reStyle.sub("", s)
    s = reScript.sub("", s)
    s = reTag.sub("", s)
    s = ents_to_txt(s)
    return s


def strip_html_media(s):
    "Strip HTML but keep media filenames"
    s = reMedia.sub(" \\1 ", s)
    return strip_html(s)


def ents_to_txt(html):
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
        return text # leave as is
    return reEnts.sub(fixup, html)


def checksum(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return sha1(data).hexdigest()


# todo: add test
def field_checksum(data):
    # 32 bit unsigned number from first 8 digits of sha1 hash
    return int(checksum(strip_html_media(data).encode("utf-8"))[:8], 16)
