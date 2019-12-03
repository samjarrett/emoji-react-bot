import ssl
import slack

PHRASES = [
    ("check a box", "ballot_box_with_check"),
    ("checks a box", "ballot_box_with_check"),
    ("clickops", "three_button_mouse"),
    ("click ops", "three_button_mouse"),
    ("delete", "deleteprod"),
    ("popcorn", "popcorn"),
    ("wait", "loading"),
]


@slack.RTMClient.run_on(event="message")
def on_message(**payload):
    data = payload["data"]
    web_client = payload["web_client"]
    text = data.get("text", "").lower()

    for phrase, emoji in PHRASES:
        if phrase in text:
            web_client.reactions_add(
                channel=data["channel"], timestamp=data["ts"], name=emoji
            )


def get_bot(token: str) -> slack.RTMClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    rtm_client = slack.RTMClient(token=token, ssl=ssl_context)

    return rtm_client
