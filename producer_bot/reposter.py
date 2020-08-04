from typing import Dict
from collections import namedtuple
import re

from slack import WebClient

from slack_helper import channel_name

RepostablePhrase = namedtuple(
    "RepostablePhrase", "match channel description emoji ephemeral"
)
REPOST_PHRASES = frozenset(
    {
        RepostablePhrase(
            match=r"corona\s?virus|covid|quarantine|isolat(ion|e)",
            channel="CUZJRJ42E",
            description="the COVID-19 pandemic",
            emoji="mask-parrot",
            ephemeral=False,
        ),
    }
)

WATCH_EMOJIS: Dict[str, RepostablePhrase] = {
    phrase.emoji: phrase for phrase in REPOST_PHRASES
}

EXCLUDE_CHANNEL_NAME = r"firehose$"


def repost(
    channel: str, timestamp: str, phrase: RepostablePhrase, web_client: WebClient,
):
    permalink = web_client.chat_getPermalink(
        channel=channel, message_ts=timestamp
    ).data["permalink"]

    # Copy the message
    posted_message = web_client.chat_postMessage(
        channel=phrase.channel, text=f":{phrase.emoji}: {permalink}", unfurl_links=True,
    )

    # Tell the poster about it
    return web_client.chat_getPermalink(
        channel=posted_message.data["channel"], message_ts=posted_message.data["ts"],
    ).data["permalink"]


def trigger(channel: str, timestamp: str, user: str, text: str, web_client: WebClient):
    name = channel_name(channel, web_client)
    if re.match(EXCLUDE_CHANNEL_NAME, name):
        return

    for phrase in REPOST_PHRASES:
        if phrase.channel == channel:
            continue  # don't try and repost in the same channel

        if re.search(phrase.match, text):
            permalink = repost(channel, timestamp, phrase, web_client)

            message = (
                f":{phrase.emoji}: hey <@{user}>, since your message was about *{phrase.description}*, "
                f"I went ahead and <{permalink}|reposted it> to <#{phrase.channel}> for you."
            )
            if phrase.ephemeral:
                web_client.chat_postEphemeral(channel=channel, user=user, text=message)
            else:
                web_client.chat_postMessage(
                    channel=channel, thread_ts=timestamp, text=message
                )
