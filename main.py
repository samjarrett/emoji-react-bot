import os
import producer_bot

BOT = producer_bot.get_bot(os.environ["SLACK_API_TOKEN"])

if __name__ == "__main__":
    BOT.start()
