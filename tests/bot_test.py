import io
import os
import sys
import tempfile
import unittest

import asynctest
import yaml

from unittest.mock import patch, MagicMock, ANY as _
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.join(os.getcwd(), 'tda_api_helper'))
print(os.path.join(os.getcwd(), 'tda_api_helper'))

from tda_api_helper.bot import HelperBot, main as bot_main
from tda_api_helper.models import Base, User, TriggeredPrompt, get_engine


class DummyDiscordUser:
    def __init__(self, discord_user_id, discord_username):
        self.id = discord_user_id
        self.name = discord_username

class DummyDiscordMessage(MagicMock):
    @classmethod
    def create(self, dummy_discord_author, content):
        message = DummyDiscordMessage()

        message.author = dummy_discord_author
        message.content = content

        return message

    async def reply(self, reply_str):
        # self.reply is a mock method created by MagicMock
        self.sync_reply(reply_str)


TEST_BOT_USER_ID = 10001
TEST_BOT_USER_NAME = 'test-bot'


class HelperBotTest(asynctest.TestCase):

    async def setUp(self):
        self.config = {
                'prompts': {
                    'prompt-1-name': {
                        'triggers': [
                            'prompt 1 trigger phrase 1',
                            'prompt 1 trigger phrase 2',
                        ],
                        'response': 'prompt 1 response'
                    },
                    'prompt-2-name': {
                        'triggers': [
                            'prompt 2 trigger phrase 1',
                            'prompt 2 trigger phrase 2',
                        ],
                        'response':  'prompt 2 response'
                    },
                }
        }

        self.tmp_db = tempfile.NamedTemporaryFile()
        self.engine = get_engine(self.tmp_db.name)
        self.session = sessionmaker(bind=self.engine)()
        Base.metadata.create_all(self.engine)

        self.helper = HelperBot(self.config, self.engine)
        self.user = DummyDiscordUser(TEST_BOT_USER_ID, TEST_BOT_USER_NAME)
        # XXX HACK: Reaching into the discord.py Client object because the user
        # field is an attribute that doesn't let itself be deleted or directly
        # modified.
        self.helper._connection.user = self.user

        await self.helper.on_ready()


    async def test_ignore_messages_by_bot(self):
        message = DummyDiscordMessage.create(
                self.user, 'prompt 1 trigger phrase 1')
        await self.helper.on_message(message)
        message.sync_reply.assert_not_called()


    async def test_message_no_trigger(self):
        message = DummyDiscordMessage.create(
                DummyDiscordUser(1, 'username'),
                'unremarkable message')

        await self.helper.on_message(message)

        message.sync_reply.assert_not_called()


    async def test_message_new_user(self):
        message = DummyDiscordMessage.create(
                DummyDiscordUser(1001, 'username'),
                'message containing prompt 1 trigger phrase 1')

        await self.helper.on_message(message)

        message.sync_reply.assert_called_once_with('prompt 1 response')

        user = User.get_user_with_discord_id(self.session, 1001)
        self.assertEqual(user.discord_username, 'username')
        self.assertEqual(user.discord_id, 1001)

        prompts = User.get_triggered_prompt_for_user(
                self.session, 'prompt-1-name',
                1001)
        self.assertEqual(1, len(prompts))
        prompt = prompts[0]

        self.assertEqual(prompt.user_id, user.id)
        self.assertEqual(prompt.prompt_name, 'prompt-1-name')
        self.assertEqual(
                prompt.trigger_message,
                'message containing prompt 1 trigger phrase 1')
        self.assertEqual(prompt.trigger_string, 'prompt 1 trigger phrase 1')


    async def test_message_message_seen_twice(self):
        # First message
        message = DummyDiscordMessage.create(
                DummyDiscordUser(1001, 'username'),
                'message containing prompt 1 trigger phrase 1')

        await self.helper.on_message(message)
        message.sync_reply.assert_called_once_with('prompt 1 response')

        # Second message
        message = DummyDiscordMessage.create(
                DummyDiscordUser(1001, 'username'),
                'message containing prompt 1 trigger phrase 1')

        await self.helper.on_message(message)
        message.sync_reply.assert_not_called()


    async def test_message_multiple_users(self):
        # User 1 triggers
        message = DummyDiscordMessage.create(
                DummyDiscordUser(1001, 'username'),
                'message containing prompt 1 trigger phrase 1')

        await self.helper.on_message(message)

        message.sync_reply.assert_called_once_with('prompt 1 response')

        user_1001 = User.get_user_with_discord_id(self.session, 1001)
        self.assertEqual(user_1001.discord_username, 'username')
        self.assertEqual(user_1001.discord_id, 1001)

        prompts = User.get_triggered_prompt_for_user(
                self.session, 'prompt-1-name',
                1001)
        self.assertEqual(1, len(prompts))
        prompt = prompts[0]

        self.assertEqual(prompt.user_id, user_1001.id)
        self.assertEqual(prompt.prompt_name, 'prompt-1-name')
        self.assertEqual(
                prompt.trigger_message,
                'message containing prompt 1 trigger phrase 1')
        self.assertEqual(prompt.trigger_string, 'prompt 1 trigger phrase 1')


        # User 2 triggers
        message = DummyDiscordMessage.create(
                DummyDiscordUser(1002, 'username'),
                'message containing prompt 2 trigger phrase 1')

        await self.helper.on_message(message)

        message.sync_reply.assert_called_once_with('prompt 2 response')

        user_1002 = User.get_user_with_discord_id(self.session, 1002)
        self.assertEqual(user_1002.discord_username, 'username')
        self.assertEqual(user_1002.discord_id, 1002)

        prompts = User.get_triggered_prompt_for_user(
                self.session, 'prompt-2-name',
                1002)
        self.assertEqual(1, len(prompts))
        prompt = prompts[0]

        self.assertEqual(prompt.user_id, user_1002.id)
        self.assertEqual(prompt.prompt_name, 'prompt-2-name')
        self.assertEqual(
                prompt.trigger_message,
                'message containing prompt 2 trigger phrase 1')
        self.assertEqual(prompt.trigger_string, 'prompt 2 trigger phrase 1')


    async def test_message_multiple_message_types(self):
        # Prompt 1
        message = DummyDiscordMessage.create(
                DummyDiscordUser(1001, 'username'),
                'message containing prompt 1 trigger phrase 1')

        await self.helper.on_message(message)

        message.sync_reply.assert_called_once_with('prompt 1 response')

        user = User.get_user_with_discord_id(self.session, 1001)
        self.assertEqual(user.discord_username, 'username')
        self.assertEqual(user.discord_id, 1001)

        prompts = User.get_triggered_prompt_for_user(
                self.session, 'prompt-1-name',
                1001)
        self.assertEqual(1, len(prompts))
        prompt = prompts[0]

        self.assertEqual(prompt.user_id, user.id)
        self.assertEqual(prompt.prompt_name, 'prompt-1-name')
        self.assertEqual(
                prompt.trigger_message,
                'message containing prompt 1 trigger phrase 1')
        self.assertEqual(prompt.trigger_string, 'prompt 1 trigger phrase 1')

        # Prompt 2
        message = DummyDiscordMessage.create(
                DummyDiscordUser(1001, 'username'),
                'message containing prompt 2 trigger phrase 1')

        await self.helper.on_message(message)

        message.sync_reply.assert_called_once_with('prompt 2 response')

        prompts = User.get_triggered_prompt_for_user(
                self.session, 'prompt-2-name',
                1001)
        self.assertEqual(1, len(prompts))
        prompt = prompts[0]

        self.assertEqual(prompt.user_id, user.id)
        self.assertEqual(prompt.prompt_name, 'prompt-2-name')
        self.assertEqual(
                prompt.trigger_message,
                'message containing prompt 2 trigger phrase 1')
        self.assertEqual(prompt.trigger_string, 'prompt 2 trigger phrase 1')


    @asynctest.patch('tda_api_helper.bot.HelperBot')
    def test_main_run(self, mock_helper_bot):
        tmp_db = tempfile.NamedTemporaryFile()

        config_file = tempfile.NamedTemporaryFile()
        config_file.write(yaml.safe_dump(self.config).encode('utf-8'))
        config_file.flush()

        args = [
                'run',
                '--token', 'discord-token',
                '--config', config_file.name,
                '--sqlite_db_file', tmp_db.name,
        ]
        bot_main(args)

        mock_helper_bot.assert_called_once_with(self.config, _)


    def test_main_init(self):
        tmp_db = tempfile.NamedTemporaryFile()

        config_file = tempfile.NamedTemporaryFile()
        config_file.write(yaml.safe_dump(self.config).encode('utf-8'))
        config_file.flush()

        args = [
                'init',
                '--sqlite_db_file', tmp_db.name,
        ]
        bot_main(args)

        self.assertGreater(os.path.getsize(tmp_db.name), 0)
