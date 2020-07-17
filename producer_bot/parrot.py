import logging
from typing import Optional

import slack

from .slack_helper import is_user_a_bot

TRIGGERED_EMOJI: str = "rip"

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

    def on_message(
        self,
        web_client: slack.WebClient,
        text: str,
        channel: str,
        timestamp: str,
        user: str,
    ):
        """Handle messages"""
        if f":{TRIGGERED_EMOJI}:" in text and not is_user_a_bot(web_client, user):
            self.write_log_entry(web_client, f"Now parroting <@{user}>")
            self.user = user

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
        if emoji == TRIGGERED_EMOJI and not is_user_a_bot(web_client, user):
            self.write_log_entry(web_client, f"Now parroting <@{user}>")
            self.user = user
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
