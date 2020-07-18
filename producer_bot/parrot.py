import logging
from typing import Optional
import re

import slack

from .slack_helper import is_user_a_bot, is_channel_im

TRIGGERED_EMOJI = {"rip", "dumpster-fire", "wave"}

LOGGER = logging.getLogger(__name__)


class Parrot:
    """Parrot party troll mode"""

    user: Optional[str] = None
    debug_channel: Optional[str]

    def __init__(self, debug_channel: Optional[str]):
        """Initialise"""
        self.user = None
        self.debug_channel = debug_channel

    def write_log_entry(self, web_client: slack.WebClient, message: str):
        """Write a message to the admin channel and log"""
        if self.debug_channel:
            web_client.chat_postMessage(
                channel=self.debug_channel, text=f":partyparrot: {message}",
            )
        LOGGER.info(message)

    def parrot(self, web_client: slack.WebClient, user: str):
        """Parrot a new user"""
        self.write_log_entry(web_client, f"Now parroting <@{user}>")
        self.user = user

    def on_message(
        self,
        web_client: slack.WebClient,
        text: str,
        channel: str,
        timestamp: str,
        user: str,
    ):
        """Handle messages"""
        if is_user_a_bot(web_client, user):
            return

        for emoji in TRIGGERED_EMOJI:
            if f":{emoji}:" in text and user != self.user:
                self.parrot(web_client, user)
                break

    def on_app_mention(
        self,
        web_client: slack.WebClient,
        text: str,
        channel: str,
        timestamp: str,
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

                self.user = None
                self.write_log_entry(
                    web_client, f"No longer parroting <@{user}> :pouting_cat:"
                )
                web_client.chat_postMessage(
                    channel=channel,
                    thread_ts=timestamp,
                    text=f"<@{user}> OK. :pouting_cat:",
                )
                break

        if channel == self.debug_channel or is_channel_im(channel, web_client):
            match = re.search(r"parrot \<\@([a-z0-9]+)\>", text)
            if match:
                self.parrot(web_client, match[1].upper())

            if "parrot status" in text:
                if self.user:
                    web_client.chat_postMessage(
                        channel=channel,
                        thread_ts=timestamp,
                        text=f":partyparrot: Currently parroting <@{self.user}>",
                    )
                else:
                    web_client.chat_postMessage(
                        channel=channel,
                        thread_ts=timestamp,
                        text=":pouting_cat: Not parroting anyone right now",
                    )

    def on_reaction_added(
        self,
        web_client: slack.WebClient,
        emoji: str,
        channel: str,
        timestamp: str,
        user: str,
    ):
        """Handle reactions added"""
        # Don't parrot bots
        if is_user_a_bot(web_client, user):
            return

        for check_emoji in TRIGGERED_EMOJI:
            if emoji == check_emoji and user != self.user:
                self.parrot(web_client, user)
                return  # don't parrot the parrot emoji itself

        if user != self.user:
            return

        web_client.reactions_add(channel=channel, timestamp=timestamp, name=emoji)

    def on_reaction_removed(
        self,
        web_client: slack.WebClient,
        emoji: str,
        channel: str,
        timestamp: str,
        user: str,
    ):
        """Handle reactions removed"""
        if user != self.user:
            return

        web_client.reactions_remove(name=emoji, channel=channel, timestamp=timestamp)

    async def on_user_typing(
        self, rtm_client: slack.RTMClient, channel: str, user: str
    ):
        """Handle users typing"""
        if user != self.user:
            return

        await rtm_client.typing(channel=channel)
