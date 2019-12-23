from random import randint
import ssl
import slack
import re
from typing import Dict

PHRASES = [
    ("buyers?", "back"),
    ("(checks? a box|checking a box)", "ballot_box_with_check"),
    ("click\s?ops", "three_button_mouse"),
    ("delete", "deleteprod"),
    ("does anyone", "plus1"),
    ("\\#experience.*", "man-tipping-hand"),
    ("(popcorn|tea)", "popcorn"),
    ("popcorn", "tea"),
    ("(saddens|saddened)", "facepalm"),
    ("real\s?deal", "tm"),
    ("wait", "loading"),
    ("wheel", "ferris_wheel"),
    ("workplace", "tr"),
    ("(place|house)", "house"),
    ("under (a|the) bus", "bus"),
    ("slow", "hourglass_flowing_sand"),
    ("pizza", "pineapple"),
    ("complicated", "man-gesturing-no"),
]

DICE_REACTIONS = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]


def num2word(num: int):
    num = str(num)
    i = 0
    while i < len(num):
        character = int(num[i])
        yield DICE_REACTIONS[character]
        i += 1


@slack.RTMClient.run_on(event="message")
def on_message(data: Dict, web_client: slack.WebClient, **kwargs):
    # handle different structure of edited messages correctly
    message = data.get("message", data)
    text = message.get("text", "").lower()

    for phrase, emoji in PHRASES:
        if re.search(phrase, text):
            web_client.reactions_add(
                channel=data["channel"], timestamp=message["ts"], name=emoji
            )

    if "dice" in text:
        roll = randint(1, 20)
        emojis = num2word(roll)

        if roll == 11:  # handle duplicate emoji reaction
            emojis = ["one", "one-again"]

        for emoji in emojis:
            web_client.reactions_add(
                channel=data["channel"], timestamp=message["ts"], name=emoji
            )


def get_bot(token: str) -> slack.RTMClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    rtm_client = slack.RTMClient(token=token, ssl=ssl_context)

    return rtm_client
