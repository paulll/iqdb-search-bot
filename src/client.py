from telethon import TelegramClient, events, sync, connection
from .secrets import api_id, api_hash, bot_token

client = TelegramClient(
	'iqdb-bot',
	api_id,
	api_hash
)

client.parse_mode = 'html'
client.start(bot_token=bot_token)
