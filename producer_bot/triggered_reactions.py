import re

from slack_sdk import WebClient

PHRASES = [
    (r"buyers?", "back"),
    (r"(checks? a box|checking a box)", "ballot_box_with_check"),
    (r"click\s?ops", "three_button_mouse"),
    (r"delete", "deleteprod"),
    (r"does anyone", "plus1"),
    (r"\#experience.*", "man-tipping-hand"),
    (r"\b(tea)\b", "popcorn"),
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
    (
        r"(\btp\b|(toilet|bog)\s?(paper|roll))",
        ["toilet-paper", "shopping_trolley"],
    ),
    (r"animal crossing", "animal-crossing"),
    (r"\bnook\b", "nook"),
    (r"\bgood bot\b", "hugging_face"),
    (r"\bbad bot\b", "anger"),
    (r"strong(ly)? ask", "muscle"),
    (r"d11s", "dandy"),
    (r"\bsage\b", "sage"),
    (r"yikes", ["yikes", "plus1"]),
]


def handle_message(channel: str, timestamp: int, text: str, web_client: WebClient):
    for phrase, emoji_to_add in PHRASES:
        if re.search(phrase, text):
            if not isinstance(emoji_to_add, list):
                emoji_to_add = [emoji_to_add]

            for emoji in emoji_to_add:
                web_client.reactions_add(
                    channel=channel, timestamp=timestamp, name=emoji
                )
