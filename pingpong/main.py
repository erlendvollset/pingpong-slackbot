import os

from cognite.client import CogniteClient
from slack_sdk.rtm_v2 import RTMClient

from pingpong.cdf_backend import CDFBackend
from pingpong.data_classes import Sport
from pingpong.pingpong_service import PingPongService
from pingpong.slackbot import PingPongSlackBot

ROOT_ASSET_EXTERNAL_ID = "Cogniters"
PINGPONG_CHANNEL_ID = "C8MAMM6AC"
ADMIN_CHANNEL_ID = "C02H9J7BP97"
ERLEND_ADMIN_CHANNEL_ID = "D8J3CN9DX"
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]


def main() -> None:
    cdf_backend = CDFBackend(
        sport=Sport.PING_PONG, root_asset_external_id=ROOT_ASSET_EXTERNAL_ID, cognite_client=CogniteClient()
    )
    ping_pong_service = PingPongService(cdf_backend=cdf_backend)
    rtm = RTMClient(token=SLACK_BOT_TOKEN)
    answer_in_channels = {PINGPONG_CHANNEL_ID, ADMIN_CHANNEL_ID, ERLEND_ADMIN_CHANNEL_ID}
    slackbot = PingPongSlackBot(ping_pong_service, rtm, answer_in_channels=answer_in_channels)

    slackbot.start()


if __name__ == "__main__":
    main()
