from random import random
import logging
from typing import Optional
import re
import urllib.parse
from dataclasses import dataclass

from slack_sdk import WebClient
from slack_sdk.rtm import RTMClient

from .slack_helper import is_user_a_bot, is_channel_im

TRIGGERED_EMOJI = {
    "wave": 0.1,
    "clap": 0.1,
    "plus1": 0.1,
    "laughing": 0.1,
    "robot_face": 0.2,
    "surprisedpikachu": 0.5,
    "facepalm": 0.5,
    "10x": 0.5,
    "jnbow": 0.8,
    "rip": 1,
    "dumpster-fire": 1,
}
MOCK_FREQUENCY = 7
TYPING_FREQUENCY = 3
PARROT_LIMIT = 50

LOGGER = logging.getLogger(__name__)


@dataclass
class MessageDetails:
    """Details of a message"""

    channel: str
    timestamp: str


class Parrot:
    """Parrot party troll mode"""

    user: Optional[str] = None
    message_count: int = 0
    debug_channel: Optional[str]

    def __init__(self, debug_channel: Optional[str]):
        """Initialise"""
        self.user = None
        self.debug_channel = debug_channel

    def write_log_entry(self, web_client: WebClient, message: str):
        """Write a message to the admin channel and log"""
        if self.debug_channel:
            web_client.chat_postMessage(
                channel=self.debug_channel,
                text=f":partyparrot: {message}",
                unfurl_links=True,
            )
        LOGGER.info(message)

    def parrot(
        self,
        web_client: WebClient,
        user: str,
        nominating_user: Optional[str] = None,
        message_details: Optional[MessageDetails] = None,
    ):
        """Parrot a new user"""
        message = f"Now parroting <@{user}>"
        if nominating_user:
            message = f"{message} - nominated by <@{nominating_user}>"

        if message_details:
            permalink = web_client.chat_getPermalink(
                channel=message_details.channel, message_ts=message_details.timestamp
            ).data["permalink"]
            message = f"{message} ({permalink})"
        self.write_log_entry(web_client, message)
        self.user = user
        self.message_count = 0

    def on_message(
        self,
        web_client: WebClient,
        text: str,
        channel: str,
        timestamp: str,
        user: str,
    ):
        """Handle messages"""
        if is_user_a_bot(web_client, user):
            return

        for emoji, chance in TRIGGERED_EMOJI.items():
            if f":{emoji}:" in text and random() <= chance and user != self.user:
                self.parrot(
                    web_client, user, message_details=MessageDetails(channel, timestamp)
                )
                return

        if user == self.user:
            self.message_count += 1
            if self.message_count % MOCK_FREQUENCY == 0:
                url = "https://mock.sam.wtf/" + urllib.parse.quote_plus(text)
                web_client.chat_postMessage(
                    channel=channel,
                    thread_ts=timestamp,
                    blocks=[
                        {
                            "type": "image",
                            "image_url": url,
                            "alt_text": text,
                        }
                    ],
                )
            if self.message_count >= PARROT_LIMIT:
                self.write_log_entry(
                    web_client,
                    f"No longer parroting <@{self.user}> :bongoblob:",
                )
                self.user = None

    def on_app_mention(
        self,
        web_client: WebClient,
        text: str,
        channel: str,
        timestamp: Optional[str],
        user: str,
    ):
        """Handle mentions"""
        phrases = {"quit it", "cut it out", "cut that out", "stop it", "enough"}
        for phrase in phrases:
            if phrase in text:
                if not self.user:
                    web_client.chat_postMessage(
                        channel=channel,
                        thread_ts=timestamp,
                        text=f"<@{user}> I'm sorry but I'm not quite sure what you're talking about?",
                    )
                    return

                self.write_log_entry(
                    web_client,
                    f"No longer parroting <@{self.user}> :pouting_cat: (<@{user}> asked me to stop)",
                )
                self.user = None
                web_client.chat_postMessage(
                    channel=channel,
                    thread_ts=timestamp,
                    text=f"<@{user}> OK. :pouting_cat:",
                )
                break

        if channel == self.debug_channel or is_channel_im(channel, web_client):
            match = re.search(r"parrot \<\@([a-z0-9]+)\>", text)
            if match:
                victim = match[1].upper()
                self.parrot(web_client, victim, user)
                web_client.chat_postEphemeral(
                    channel=channel,
                    thread_ts=timestamp,
                    user=user,
                    text=f":partyparrot: Watch out <@{victim}>, there's a parrot circling you",
                )

            if "parrot status" in text:
                if self.user:
                    web_client.chat_postEphemeral(
                        channel=channel,
                        thread_ts=timestamp,
                        user=user,
                        text=f":partyparrot: Currently parroting <@{self.user}>",
                    )
                else:
                    web_client.chat_postEphemeral(
                        channel=channel,
                        thread_ts=timestamp,
                        user=user,
                        text=":pouting_cat: Not parroting anyone right now",
                    )

    def on_reaction_added(
        self,
        web_client: WebClient,
        emoji: str,
        channel: str,
        timestamp: str,
        user: str,
    ):
        """Handle reactions added"""
        # Don't parrot bots
        if is_user_a_bot(web_client, user):
            return

        for check_emoji, chance in TRIGGERED_EMOJI.items():
            if emoji == check_emoji and random() <= chance and user != self.user:
                self.parrot(
                    web_client, user, message_details=MessageDetails(channel, timestamp)
                )
                return  # don't parrot the parrot emoji itself

        if user != self.user:
            return

        web_client.reactions_add(channel=channel, timestamp=timestamp, name=emoji)

    def on_reaction_removed(
        self,
        web_client: WebClient,
        emoji: str,
        channel: str,
        timestamp: str,
        user: str,
    ):
        """Handle reactions removed"""
        if user != self.user:
            return

        web_client.reactions_remove(name=emoji, channel=channel, timestamp=timestamp)

    async def on_user_typing(self, rtm_client: RTMClient, channel: str, user: str):
        """Handle users typing"""
        if user != self.user:
            return

        if self.message_count % TYPING_FREQUENCY == 0:
            await rtm_client.typing(channel=channel)
