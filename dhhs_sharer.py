import os
import logging
import time
import ssl

from dotenv import load_dotenv
import requests
import slack


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(module)s:%(funcName)s %(message)s",
)

SLACK_API_TOKEN = os.environ["SLACK_API_TOKEN"]
TWITTER_API_TOKEN = os.environ["TWITTER_API_TOKEN"]
DHHS_CHANNEL = os.environ["DHHS_CHANNEL"]


def get_slack_client(token: str) -> slack.WebClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    return slack.WebClient(token=token, ssl=ssl_context)


def main():
    """The main entry point"""
    slack_client = get_slack_client(SLACK_API_TOKEN)

    try:
        with open("last-id.txt", "r") as last_id_file:
            last_id = last_id_file.read()
    except FileNotFoundError:
        last_id = None

    headers = {"Authorization": f"Bearer {TWITTER_API_TOKEN}"}
    params = {"q": "from:@VicGovDHHS #Covid19VicData", "include_entities": "false"}

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
        logging.info(f"Found new message with ID: {last_id}")

        with open("last-id.txt", "w") as last_id_file:
            last_id_file.write(last_id)

        slack_client.chat_postMessage(
            channel=DHHS_CHANNEL,
            text=f":chottie: https://twitter.com/vicgovdhhs/status/{last_id}",
            unfurl_links=True,
            unfurl_media=True,
        )


if __name__ == "__main__":
    main()
