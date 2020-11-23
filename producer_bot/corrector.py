from collections import namedtuple
import re

from slack import WebClient

CorrectablePhrase = namedtuple(
    "CorrectablePhrase", "match message emoji name ephemeral"
)
CORRECT_PHRASES = frozenset(
    {
        CorrectablePhrase(
            match=r"\bgarage\b",
            message="> garbage\nFTFY :welcome:",
            emoji="thinking_face",
            name="Corrector",
            ephemeral=False,
        ),
        CorrectablePhrase(
            match=r"\bbrighton\b",
            message="> Braaaahton\nFTFY :welcome:",
            emoji="beach_with_umbrella",
            name="Corrector",
            ephemeral=False,
        ),
        CorrectablePhrase(
            match=r"\bfriday\b",
            message="https://www.youtube.com/watch?v=kfVsfOSbJY0&feature=youtu.be",
            emoji="rebecca",
            name="RB",
            ephemeral=False,
        ),
        CorrectablePhrase(
            match=r"\bsaturday\b",
            message="https://www.youtube.com/watch?v=GVCzdpagXOQ&feature=youtu.be",
            emoji="rebecca",
            name="RB",
            ephemeral=False,
        ),
    }
)


def trigger(channel: str, timestamp: int, user: str, text: str, web_client: WebClient):
    for phrase in CORRECT_PHRASES:
        if re.search(phrase.match, text):
            if phrase.ephemeral:
                web_client.chat_postEphemeral(
                    channel=channel,
                    user=user,
                    text=phrase.message,
                    icon_emoji=phrase.emoji,
                    username=phrase.name,
                )
            else:
                web_client.chat_postMessage(
                    channel=channel,
                    thread_ts=timestamp,
                    text=phrase.message,
                    icon_emoji=phrase.emoji,
                    username=phrase.name,
                    unfurl_links=True,
                )
