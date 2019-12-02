import ssl
import slack

PHRASES = [
    ("delete", "deleteprod"),
    ("check a box", "ballot_box_with_check"),
]


@slack.RTMClient.run_on(event="message")
def on_message(**payload):
    data = payload["data"]
    web_client = payload["web_client"]
    text = data.get("text", "")

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
