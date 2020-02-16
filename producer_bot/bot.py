import logging
from random import randint
import os
import re
import ssl
from typing import Dict
import slack
from .version import get_version
from .slack_helper import (
    event_item_to_reactions_api,
    get_bot_user_id,
    get_bot_reactions,
)

DEBUG_CHANNEL = os.environ.get("DEBUG_CHANNEL")
BOT_VERSION = get_version()

BACKTRACK_EMOJI = "no_entry_sign"

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

EMOJI_VERBIAGE = {
    "add": "added",
    "remove": "removed",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(module)s:%(funcName)s %(message)s",
)


def num2word(num: int):
    num = str(num)
    i = 0
    while i < len(num):
        character = int(num[i])
        yield DICE_REACTIONS[character]
        i += 1


@slack.RTMClient.run_on(event="hello")
def on_hello(**kwargs):  # pylint: disable=unused-argument
    logging.info("Bot connected to the server")


@slack.RTMClient.run_on(event="goodbye")
def on_goodbye(**kwargs):  # pylint: disable=unused-argument
    logging.info(
        "Server requested the bot disconnect - will automatically reconnect shortly"
    )


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


@slack.RTMClient.run_on(event="reaction_added")
def on_reaction_added(
    data: Dict, web_client: slack.WebClient, **kwargs
):  # pylint: disable=unused-argument
    if data["reaction"] == BACKTRACK_EMOJI:
        reactions_item, item_type = event_item_to_reactions_api(data["item"])
        bot_id = get_bot_user_id(web_client)

        bot_reactions = get_bot_reactions(web_client, bot_id, item_type, reactions_item)

        for reaction in bot_reactions:
            web_client.reactions_remove(name=reaction.get("name"), **reactions_item)


@slack.RTMClient.run_on(event="emoji_changed")
def on_emoji_changed(
    data: Dict, web_client: slack.WebClient, **kwargs
):  # pylint: disable=unused-argument
    if not DEBUG_CHANNEL:
        return

    verb = EMOJI_VERBIAGE.get(data["subtype"], data["subtype"])

    if "alias:" in data.get("value", ""):
        verb = f"alias {verb}"

    # create a string of the affected emojis comma separated until the penultimate, and then and'ed
    emoji_names = [f":{emoji}:" for emoji in data.get("names", [data.get("name")])]
    emojis = ", ".join(emoji_names)

    web_client.chat_postMessage(
        channel=DEBUG_CHANNEL, text=f":robot_face: Emoji {verb}: `{emojis}` ({emojis})",
    )


def get_bot(token: str) -> slack.RTMClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    rtm_client = slack.RTMClient(token=token, ssl=ssl_context)

    return rtm_client
