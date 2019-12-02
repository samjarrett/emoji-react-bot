import slack
import ssl

@slack.RTMClient.run_on(event='message')
def on_message(**payload):
    data = payload['data']
    web_client = payload['web_client']
    rtm_client = payload['rtm_client']

    if 'delete' in data.get('text', []):
        channel_id = data['channel']
        thread_ts = data['ts']
        user = data['user']

        web_client.reactions_add(
            channel=data['channel'],
            timestamp=data['ts'],
            name="deleteprod"
        )

def get_bot(token: str) -> slack.RTMClient:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    rtm_client = slack.RTMClient(token=token, ssl=ssl_context)

    return rtm_client
