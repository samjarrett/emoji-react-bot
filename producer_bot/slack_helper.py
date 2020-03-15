from copy import deepcopy
from typing import Dict
from functools import lru_cache
import slack
from .helpers import BlackBox


def event_item_to_reactions_api(item: Dict) -> Dict:
    reaction = deepcopy(item)
    reaction["timestamp"] = reaction.pop("ts")
    item_type = reaction.pop("type")

    return reaction, item_type


def get_bot_user_id(web_client: slack.WebClient) -> str:
    return __cached_get_bot_user_id(BlackBox(web_client))


def is_channel_private(channel: str, web_client: slack.WebClient) -> bool:
    return __cached_is_channel_private(channel, BlackBox(web_client))


@lru_cache(maxsize=None)
def __cached_get_bot_user_id(web_client: BlackBox) -> str:
    return web_client.contents.auth_test().get("user_id")


@lru_cache(maxsize=None)
def __cached_is_channel_private(channel: str, web_client: BlackBox) -> str:
    return (
        web_client.contents.conversations_info(channel=channel)
        .get("channel", {})
        .get("is_private", True)
    )


def get_bot_reactions(
    web_client: slack.WebClient, bot_user_id: str, item_type: str, item: Dict
):
    reaction_response = web_client.reactions_get(**item)

    reactions = reaction_response.get(item_type).get("reactions")

    return filter(lambda reaction: bot_user_id in reaction.get("users", []), reactions)
