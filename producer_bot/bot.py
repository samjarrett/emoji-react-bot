import logging
import os
import ssl
from typing import Dict
import slack_sdk
from slack_sdk.rtm import RTMClient
from .slack_helper import (
    event_item_to_reactions_api,
    get_bot_user_id,
    is_channel_im,
    get_bot_reactions,
)
from . import triggered_reactions
from . import dice_roller
from . import corrector
from .parrot import Parrot
from .version import get_version

DEBUG_CHANNEL = os.environ.get("DEBUG_CHANNEL", "")
ADMIN_DEBUG_CHANNEL = os.environ.get("ADMIN_DEBUG_CHANNEL", "")
ANNOUNCEMENT_CHANNEL = os.environ.get("ANNOUNCEMENT_CHANNEL", "")

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


@RTMClient.run_on(event="hello")
def on_hello(
    web_client: slack_sdk.WebClient, **kwargs
):  # pylint: disable=unused-argument
    logging.info("Bot connected to the server")
    web_client.chat_postMessage(
        channel=ADMIN_DEBUG_CHANNEL,
        text=f":hello-my-name-is: Bot version {get_version()} connected",
    )


@RTMClient.run_on(event="goodbye")
def on_goodbye(**kwargs):  # pylint: disable=unused-argument
    logging.info(
        "Server requested the bot disconnect - will automatically reconnect shortly"
    )


@RTMClient.run_on(event="message")
def on_message(
    data: Dict, web_client: slack_sdk.WebClient, **kwargs
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
    except slack_sdk.errors.SlackApiError as exception:
        logging.error(exception)

    if "dice" in text:
        try:
            dice_roller.roll(channel, timestamp, web_client)
        except slack_sdk.errors.SlackApiError as exception:
            logging.error(exception)

    try:
        corrector.trigger(channel, timestamp, user, text, web_client)
    except slack_sdk.errors.SlackApiError as exception:
        logging.error(exception)

    try:
        if "bot_id" not in data:  # don't trigger on bots
            bot_user_id = get_bot_user_id(web_client).lower()
            if text.startswith(f"<@{bot_user_id}>") or is_channel_im(
                channel, web_client
            ):
                PARROT.on_app_mention(
                    web_client, text, channel, data.get("thread_ts", None), user
                )
            PARROT.on_message(web_client, text, channel, timestamp, user)
    except slack_sdk.errors.SlackApiError as exception:
        logging.error(exception)


@RTMClient.run_on(event="reaction_added")
def on_reaction_added(
    data: Dict, web_client: slack_sdk.WebClient, **kwargs
):  # pylint: disable=unused-argument
    if data["reaction"] == BACKTRACK_EMOJI:
        reactions_item, item_type = event_item_to_reactions_api(data["item"])
        bot_id = get_bot_user_id(web_client)

        bot_reactions = get_bot_reactions(web_client, bot_id, item_type, reactions_item)

        for reaction in bot_reactions:
            web_client.reactions_remove(name=reaction.get("name"), **reactions_item)

    try:
        PARROT.on_reaction_added(
            web_client,
            data["reaction"],
            data["item"]["channel"],
            data["item"]["ts"],
            data["user"],
        )
    except slack_sdk.errors.SlackApiError as exception:
        logging.error(exception)


@RTMClient.run_on(event="reaction_removed")
def on_reaction_removed(
    data: Dict, web_client: slack_sdk.WebClient, **kwargs
):  # pylint: disable=unused-argument
    try:
        PARROT.on_reaction_removed(
            web_client,
            data["reaction"],
            data["item"]["channel"],
            data["item"]["ts"],
            data["user"],
        )
    except slack_sdk.errors.SlackApiError as exception:
        logging.error(exception)


@RTMClient.run_on(event="user_typing")
async def on_user_typing(
    data: Dict, rtm_client: RTMClient, **kwargs
):  # pylint: disable=unused-argument
    try:
        await PARROT.on_user_typing(rtm_client, data["channel"], data["user"])
    except slack_sdk.errors.SlackApiError as exception:
        logging.error(exception)


@RTMClient.run_on(event="emoji_changed")
def on_emoji_changed(
    data: Dict, web_client: slack_sdk.WebClient, **kwargs
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
        channel=DEBUG_CHANNEL,
        text=f":robot_face: Emoji {verb}: `{emojis}` ({emojis})",
    )


@RTMClient.run_on(event="channel_created")
def on_channel_created(
    data: Dict, web_client: slack_sdk.WebClient, **kwargs
):  # pylint: disable=unused-argument
    web_client.chat_postMessage(
        channel=ANNOUNCEMENT_CHANNEL,
        text=f":heavy_plus_sign: #{data['channel']['name']} created by <@{data['channel']['creator']}>",
        link_names=True,
    )


def get_bot(token: str) -> RTMClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    rtm_client = RTMClient(token=token, ssl=ssl_context)

    return rtm_client
