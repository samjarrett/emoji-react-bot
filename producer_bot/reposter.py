from collections import namedtuple
import re

from slack import WebClient

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
        )
    }
)

WATCH_EMOJIS = frozenset({phrase.emoji for phrase in REPOST_PHRASES})


def repost(
    channel: str,
    timestamp: str,
    user: str,
    phrase: RepostablePhrase,
    web_client: WebClient,
):
    permalink = web_client.chat_getPermalink(
        channel=channel, message_ts=timestamp
    ).data["permalink"]

    # Copy the message
    posted_message = web_client.chat_postMessage(
        channel=phrase.channel, text=f":{phrase.emoji}: {permalink}", unfurl_links=True,
    )

    # Tell the poster about it
    posted_permalink = web_client.chat_getPermalink(
        channel=posted_message.data["channel"], message_ts=posted_message.data["ts"],
    ).data["permalink"]

    message = (
        f":{phrase.emoji}: hey <@{user}>, since <{permalink}|your message> was about *{phrase.description}*, "
        f"I went ahead and <{posted_permalink}|reposted it> to <#{phrase.channel}> for you."
    )
    if phrase.ephemeral:
        web_client.chat_postEphemeral(channel=channel, user=user, text=message)
    else:
        web_client.chat_postMessage(channel=channel, thread_ts=timestamp, text=message)


def trigger(channel: str, timestamp: int, user: str, text: str, web_client: WebClient):
    for phrase in REPOST_PHRASES:
        if phrase.channel == channel:
            continue  # don't try and repost in the same channel

        if re.search(phrase.match, text):
            repost(channel, timestamp, user, phrase, web_client)
