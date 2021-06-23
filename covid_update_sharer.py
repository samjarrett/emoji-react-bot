import os
import logging
import hashlib
import ssl

from dotenv import load_dotenv
import requests
import slack_sdk

TRACKED_SEARCHES = {
    "from:@vicgovdh #COVID19VicData OR #EveryTestHelps": "chottie",
    'from:@NSWHealth "NSW recorded" cases': "nsw",
    'from:@qldhealthnews "Queensland #COVID19 update"': "annastacia",
    'from:@MarkMcGowanMP "This is our WA COVID-19 update"': "perth",
    'from:@minhealthnz "new cases of" "in the community in New Zealand"': "flag-nz",
}

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(module)s:%(funcName)s %(message)s",
)

SLACK_API_TOKEN = os.environ["SLACK_API_TOKEN"]
TWITTER_API_TOKEN = os.environ["TWITTER_API_TOKEN"]
DHHS_CHANNEL = os.environ["DHHS_CHANNEL"]


def get_slack_client(token: str) -> slack_sdk.WebClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    return slack_sdk.WebClient(token=token, ssl=ssl_context)


def main():
    """The main entry point"""
    slack_client = get_slack_client(SLACK_API_TOKEN)

    for query, emoji in TRACKED_SEARCHES.items():
        hashed_query = hashlib.sha1(query.encode()).hexdigest()
        last_id_filename = f"id_cache/last-id-{hashed_query}.txt"
        try:
            with open(last_id_filename, "r") as last_id_file:
                last_id = last_id_file.read()
        except FileNotFoundError:
            last_id = None

        headers = {"Authorization": f"Bearer {TWITTER_API_TOKEN}"}
        params = {
            "q": query,
            "include_entities": "false",
        }

        if last_id:
            params["since_id"] = last_id

        response = requests.get(
            "https://api.twitter.com/1.1/search/tweets.json",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        if data["statuses"]:
            last_id = data["statuses"][0]["id_str"]
            username = data["statuses"][0]["user"]["screen_name"].lower()
            logging.info(
                f"Found new {emoji} message from @{username} with ID: {last_id}"
            )

            with open(last_id_filename, "w") as last_id_file:
                last_id_file.write(last_id)

            slack_client.chat_postMessage(
                channel=DHHS_CHANNEL,
                text=f":{emoji}: https://twitter.com/{username}/status/{last_id}",
                unfurl_links=True,
                unfurl_media=True,
            )


if __name__ == "__main__":
    main()
