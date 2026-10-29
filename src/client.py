import os
from urllib.parse import urlparse

from telethon import TelegramClient, events, sync, connection
from .secrets import api_id, api_hash, bot_token

proxy = None
_proxy_url = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
if _proxy_url:
    # telethon proxy tuple: (proxy_type, addr, port)
    _u = urlparse(_proxy_url)
    proxy = (_u.scheme or 'http', _u.hostname, _u.port or 443)

client = TelegramClient(
	'iqdb-bot',
	api_id,
	api_hash,
	proxy=proxy
)

client.parse_mode = 'html'
client.start(bot_token=bot_token)
