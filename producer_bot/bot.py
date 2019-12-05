import ssl
import slack
import re

PHRASES = [
    ("buyers?", "back"),
    ("(checks? a box|checking a box)", "ballot_box_with_check"),
    ("click\s?ops", "three_button_mouse"),
    ("delete", "deleteprod"),
    ("does anyone", "plus1"),
    ("\\#experience.*", "man-tipping-hand"),
    ("popcorn", "popcorn"),
    ("(saddens|saddened)", "facepalm"),
    ("wait", "loading"),
    ("wheel", "ferris_wheel"),
    ("workplace", "tr"),
]


@slack.RTMClient.run_on(event="message")
def on_message(**payload):
    data = payload["data"]
    web_client = payload["web_client"]
    text = data.get("text", "").lower()

    for phrase, emoji in PHRASES:
        if re.search(phrase, text):
            web_client.reactions_add(
                channel=data["channel"], timestamp=data["ts"], name=emoji
            )


def get_bot(token: str) -> slack.RTMClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    rtm_client = slack.RTMClient(token=token, ssl=ssl_context)

    return rtm_client
