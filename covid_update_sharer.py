import os
import logging
import ssl
from typing import Optional

from dotenv import load_dotenv
import requests
import slack_sdk

TRACKED_SEARCHES = [
    {
        "query": "(#COVID19VicData OR #EveryTestHelps)",
        "user": "vicgovdh",
        "emoji": "chottie",
    },
    {
        "query": '"NSW recorded" cases',
        "user": "NSWHealth",
        "emoji": "nsw",
    },
    {
        "query": '"Queensland #COVID19 update"',
        "user": "qldhealthnews",
        "emoji": "annastacia",
    },
    {
        "query": '"This is our WA COVID-19 update"',
        "user": "MarkMcGowanMP",
        "emoji": "perth",
    },
    {
        "query": '"ACT COVID-19 update"',
        "user": "ACTHealth",
        "emoji": "act-gov",
    },
    {
        "query": '"cases of" "the community today" has:media',
        "user": "covid19nz",
        "emoji": "flag-nz",
    },
]

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(module)s:%(funcName)s %(message)s",
)

SLACK_API_TOKEN = os.environ["SLACK_API_TOKEN"]
TWITTER_API_TOKEN = os.environ["TWITTER_API_TOKEN"]
POST_CHANNEL = os.environ["DHHS_CHANNEL"]

HEADERS = {"Authorization": f"Bearer {TWITTER_API_TOKEN}"}
SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

CHILD_TWEET_LIMIT = 3


def get_slack_client(token: str) -> slack_sdk.WebClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    return slack_sdk.WebClient(token=token, ssl=ssl_context)


def get_latest_post(user: str, query, last_id: Optional[str]):
    """Get the latest post"""
    query = f"from:{user} {query}"
    params = {
        "query": query,
        "tweet.fields": "created_at,id,text",
    }

    if last_id:
        params["since_id"] = last_id

    response = requests.get(
        SEARCH_URL,
        params=params,
        headers=HEADERS,
    )
    response.raise_for_status()

    data = response.json()
    if data.get("data"):
        return data["data"][0]["id"]


def get_child_posts(post_id: str, user: str):
    """Get any child post IDs"""
    params = {
        "query": f"from:{user} conversation_id:{post_id}",
        "tweet.fields": "id,text",
        "max_results": 100,
    }
    response = requests.get(
        SEARCH_URL,
        params=params,
        headers=HEADERS,
    )
    response.raise_for_status()

    data = response.json()
    if data.get("data"):
        return list(
            map(lambda tweet: tweet["id"], data["data"][:-CHILD_TWEET_LIMIT:-1])
        )


def main():
    """The main entry point"""
    slack_client = get_slack_client(SLACK_API_TOKEN)

    for search in TRACKED_SEARCHES:
        last_id_filename = f"id_cache/last-id-{search['user']}.txt"

        try:
            with open(last_id_filename, "r") as last_id_file:
                last_id = last_id_file.read()
        except FileNotFoundError:
            last_id = None

        last_id = get_latest_post(search["user"], search["query"], last_id)
        if last_id:
            logging.info(f"Found new message from @{search['user']} with ID: {last_id}")

            with open(last_id_filename, "w") as last_id_file:
                last_id_file.write(last_id)

            tweet_text = f":{search['emoji']}: https://twitter.com/{search['user']}/status/{last_id}\n"

            child_posts = [
                f"https://twitter.com/{search['user']}/status/{post_id}"
                for post_id in get_child_posts(last_id, search["user"])
            ]
            if child_posts:
                tweet_text += "\n".join(child_posts)

            slack_client.chat_postMessage(
                channel=POST_CHANNEL,
                text=tweet_text,
                unfurl_links=True,
                unfurl_media=True,
            )


if __name__ == "__main__":
    main()
