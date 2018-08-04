import os
import sys
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
sys.path.append(src_dir)
import pytest
import slackbot
from unittest import mock
import services

pingpongbot_id = "U9FID819D"
test_user = 'U6N8D853P'
test_channel = 'D8J3CN9DX'

@pytest.fixture(autouse=True)
def set_pingpongbotid():
    slackbot.pingpongbot_id = pingpongbot_id
    yield
    slackbot.pingpongbot_id = None

# @pytest.fixture
# def db_services_mock(monkeypatch):
#     dbs_mock = mock.MagicMock()
#     monkeypatch.setattr(services, "db_services", lambda _: dbs_mock)
#     yield dbs_mock


def text_to_slack_events(text):
    return [{'type': 'message', 'user': test_user, 'text': text, 'client_msg_id': 'abcd', 'team': 'T3XCNGHJL',
            'channel': test_channel, 'event_ts': '1', 'ts': '2'}]

def parse_bot_commands_params():
    return [(text_to_slack_events('<@{}> match <@KD839FK38> <@9FJ48GJF8> 11 0'.format(pingpongbot_id)),
             ("match <@KD839FK38> <@9FJ48GJF8> 11 0", test_channel, test_user)),
            (text_to_slack_events('<@{}> match <@KD839FK38> <@9FJ48GJF8> 11 0'.format("NOT_BOT_ID")),
             (None, None, None))
            ]

@pytest.mark.parametrize("test_input, expected", parse_bot_commands_params())
def test_parse_bot_commands(test_input, expected):
    assert slackbot.parse_bot_commands(test_input) == expected

@mock.patch("services.db_services.add_player")
def test_init_player(add_player_mock):
    slackbot.init_player(test_user)
    add_player_mock.assert_called_once()









