from telethon import events, functions
from .client import client

start_text = """
Hello!
Just send me an image and I'll find its source on image boards. You can also send me multiple images or hyperlinks at once
"""


@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	if message.message.startswith('/start'):
		await message.respond(start_text)
