import os
from slackclient import SlackClient

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def send_message(message, channel):
    slack_client.api_call(
        "chat.postMessage",
        channel=channel or 'G8JKTFJ6Q',
        text=message
    )

# def send_typing(channel):
#     pingpongbot_id = slack_client.api_call("auth.test")["user_id"]
#     message = {
#         "user": pingpongbot_id,
#         "type": "user_typing",
#         "channel": channel,
#     }
#     slack_client.rtm_send_message(message=message, channel=channel)