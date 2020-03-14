from random import randint

from slack import WebClient

DICE_REACTIONS = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]


def num2word(num: int):
    num = str(num)
    i = 0
    while i < len(num):
        character = int(num[i])
        yield DICE_REACTIONS[character]
        i += 1


def roll(channel: str, timestamp: int, web_client: WebClient):
    result = randint(1, 20)
    emojis = num2word(result)

    if result == 11:  # handle duplicate emoji reaction
        emojis = ["one", "one-again"]

    for emoji in emojis:
        web_client.reactions_add(channel=channel, timestamp=timestamp, name=emoji)
