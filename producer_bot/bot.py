import logging
import os
import ssl
from typing import Dict
import slack
from .slack_helper import (
    event_item_to_reactions_api,
    get_bot_user_id,
    is_channel_private,
    get_bot_reactions,
)
from . import triggered_reactions
from . import dice_roller
from . import reposter
from . import corrector
from .parrot import Parrot

DEBUG_CHANNEL = os.environ.get("DEBUG_CHANNEL")
ADMIN_DEBUG_CHANNEL = os.environ.get("ADMIN_DEBUG_CHANNEL")

BACKTRACK_EMOJI = "no_entry_sign"
EMOJI_VERBIAGE = {
    "add": "added",
    "remove": "removed",
}

PARROT = Parrot(ADMIN_DEBUG_CHANNEL)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(module)s:%(funcName)s %(message)s",
)


@slack.RTMClient.run_on(event="hello")
def on_hello(**kwargs):  # pylint: disable=unused-argument
    logging.info("Bot connected to the server")


@slack.RTMClient.run_on(event="goodbye")
def on_goodbye(**kwargs):  # pylint: disable=unused-argument
    logging.info(
        "Server requested the bot disconnect - will automatically reconnect shortly"
    )


@slack.RTMClient.run_on(event="message")
def on_message(
    data: Dict, web_client: slack.WebClient, **kwargs
):  # pylint: disable=unused-argument
    # handle different structure of edited messages correctly
    if data.get("subtype") == "message_replied":
        logging.debug("Skipping event as it's a message_replied event")
        return

    text = data.get("text", "").lower()
    channel = data["channel"]
    timestamp = data["ts"]
    user = data.get("user", "")

    try:
        triggered_reactions.handle_message(channel, timestamp, text, web_client)
    except slack.errors.SlackApiError as exception:
        logging.error(exception)

    try:
        if user and not is_channel_private(channel, web_client):
            reposter.trigger(channel, timestamp, user, text, web_client)
    except slack.errors.SlackApiError as exception:
        logging.error(exception)

    if "dice" in text:
        try:
            dice_roller.roll(channel, timestamp, web_client)
        except slack.errors.SlackApiError as exception:
            logging.error(exception)

    try:
        corrector.trigger(channel, timestamp, user, text, web_client)
    except slack.errors.SlackApiError as exception:
        logging.error(exception)

    try:
        bot_user_id = get_bot_user_id(web_client).lower()
        if "bot_id" not in data:  # don't trigger on bots
            if f"<@{bot_user_id}>" in text:
                PARROT.on_app_mention(web_client, text, channel, timestamp, user)
            PARROT.on_message(web_client, text, channel, timestamp, user)
    except slack.errors.SlackApiError as exception:
        logging.error(exception)


@slack.RTMClient.run_on(event="reaction_added")
def on_reaction_added(
    data: Dict, web_client: slack.WebClient, **kwargs
):  # pylint: disable=unused-argument
    if data["reaction"] == BACKTRACK_EMOJI:
        reactions_item, item_type = event_item_to_reactions_api(data["item"])
        bot_id = get_bot_user_id(web_client)

        bot_reactions = get_bot_reactions(web_client, bot_id, item_type, reactions_item)

        for reaction in bot_reactions:
            web_client.reactions_remove(name=reaction.get("name"), **reactions_item)

    phrase = reposter.WATCH_EMOJIS.get(data["reaction"])
    if phrase:
        permalink = reposter.repost(
            data["item"]["channel"], data["item"]["ts"], phrase, web_client
        )
        message = (
            f":{phrase.emoji}: hey <@{data['user']}>, since your message was about *{phrase.description}*, "
            f"I went ahead and <{permalink}|reposted it> to <#{phrase.channel}> for you."
        )
        web_client.chat_postEphemeral(
            channel=data["item"]["channel"], user=data["user"], text=message
        )

    try:
        PARROT.on_reaction_added(
            web_client,
            data["reaction"],
            data["item"]["channel"],
            data["item"]["ts"],
            data["user"],
        )
    except slack.errors.SlackApiError as exception:
        logging.error(exception)


@slack.RTMClient.run_on(event="reaction_removed")
def on_reaction_removed(
    data: Dict, web_client: slack.WebClient, **kwargs
):  # pylint: disable=unused-argument
    try:
        PARROT.on_reaction_removed(
            web_client,
            data["reaction"],
            data["item"]["channel"],
            data["item"]["ts"],
            data["user"],
        )
    except slack.errors.SlackApiError as exception:
        logging.error(exception)


@slack.RTMClient.run_on(event="user_typing")
async def on_user_typing(
    data: Dict, rtm_client: slack.RTMClient, **kwargs
):  # pylint: disable=unused-argument
    try:
        await PARROT.on_user_typing(rtm_client, data["channel"], data["user"])
    except slack.errors.SlackApiError as exception:
        logging.error(exception)


@slack.RTMClient.run_on(event="emoji_changed")
def on_emoji_changed(
    data: Dict, web_client: slack.WebClient, **kwargs
):  # pylint: disable=unused-argument
    if not DEBUG_CHANNEL:
        return

    verb = EMOJI_VERBIAGE.get(data["subtype"], data["subtype"])

    if "alias:" in data.get("value", ""):
        verb = f"alias {verb}"

    # create a string of the affected emojis comma separated until the penultimate, and then and'ed
    emoji_names = [f":{emoji}:" for emoji in data.get("names", [data.get("name")])]
    emojis = ", ".join(emoji_names)

    web_client.chat_postMessage(
        channel=DEBUG_CHANNEL, text=f":robot_face: Emoji {verb}: `{emojis}` ({emojis})",
    )


def get_bot(token: str) -> slack.RTMClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    rtm_client = slack.RTMClient(token=token, ssl=ssl_context)

    return rtm_client
