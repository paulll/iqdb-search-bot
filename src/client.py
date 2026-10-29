import os

from telethon import TelegramClient, events, sync, connection
from .secrets import api_id, api_hash, bot_token

proxy = None
_proxy_host = os.getenv('TELEGRAM_PROXY_HOST')
if _proxy_host:
    # telethon proxy tuple order: (proxy_type, addr, port)
    proxy = (os.getenv('TELEGRAM_PROXY_TYPE', 'http'),
             _proxy_host,
             int(os.getenv('TELEGRAM_PROXY_PORT', '7890')))

client = TelegramClient(
	'iqdb-bot',
	api_id,
	api_hash,
	proxy=proxy
)

client.parse_mode = 'html'
client.start(bot_token=bot_token)
