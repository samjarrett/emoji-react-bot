from random import randint
import re
import ssl
from typing import Dict
import slack

PHRASES = [
    (r"buyers?", "back"),
    (r"(checks? a box|checking a box)", "ballot_box_with_check"),
    (r"click\s?ops", "three_button_mouse"),
    (r"delete", "deleteprod"),
    (r"does anyone", "plus1"),
    (r"\#experience.*", "man-tipping-hand"),
    (r"(popcorn|tea)", "popcorn"),
    (r"popcorn", "tea"),
    (r"(saddens|saddened)", "facepalm"),
    (r"real\s?deal", "tm"),
    (r"wait", "loading"),
    (r"wheel", "ferris_wheel"),
    (r"workplace", "tr"),
    (r"(place|house)", "house"),
    (r"under (a|the) bus", "bus"),
    (r"slow", "hourglass_flowing_sand"),
    (r"pizza", "pineapple"),
    (r"complicated", "man-gesturing-no"),
    (r"(honk|g[oe]{2}se)", "honk"),
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
def on_message(
    data: Dict, web_client: slack.WebClient, **kwargs
):  # pylint: disable=unused-argument
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
