import aiohttp
import asyncio
import re
import aiofiles

from aiofiles.os import remove
from os.path import normpath
from pyquery import PyQuery as pq
from telethon import events, functions, Button
from telethon.tl.types import MessageMediaPhoto
from .client import client

IQDB_HOST = 'https://iqdb.org/'
#IQDB_HOST = 'https://httpbin.org/anything'
IQDB_MARKER_ERROR = '<!-- Failed...'
IQDB_MARKER_NO_RESULTS = 'No relevant matches'

session = aiohttp.ClientSession()
groups = dict()
group_replies = dict()


@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	if message.media and isinstance(message.media, MessageMediaPhoto):
		processing_msg = None
		if message.grouped_id:
			if not message.grouped_id in groups:
				groups[message.grouped_id] = 1
				group_replies[message.grouped_id] = await message.reply("Processing...")

				# state changed while replying
				if groups[message.grouped_id] != 1:
					await group_replies[message.grouped_id].edit("Processing... {} queued".format(groups[message.grouped_id]))
			else:
				groups[message.grouped_id] += 1
				if message.grouped_id in group_replies:
					await group_replies[message.grouped_id].edit("Processing... {} queued".format(groups[message.grouped_id]))
		else:
			processing_msg = await message.reply("Processing...")

		file = await message.download_media()
		form = (
			('file', open(file, 'rb')),
			('MAX_FILE_SIZE', '8388608'),
			('service[]', '1'),
			('service[]', '2'),
			('service[]', '3'),
			('service[]', '4'),
			('service[]', '5'),
			('service[]', '6'),
			('service[]', '11'),
			('service[]', '13')
		)
		resp = await session.post(IQDB_HOST, data=form)
		body = await resp.text()

		if IQDB_MARKER_ERROR in body:
			await event.message.reply('Something went wrong :c')
		elif IQDB_MARKER_NO_RESULTS in body:
			image_url = body.split('https://ascii2d.net/search/url/')[1].split('">')[0]
			buttons = client.build_reply_markup([
				[
					Button.url('Google', url='https://www.google.com/searchbyimage?image_url={}&safe=off'.format(image_url)),
					Button.url('Yandex', url='https://yandex.ru/images/search?rpt=imageview&url={}'.format(image_url))
				],
				[
					Button.url('ascii2d', url='https://ascii2d.net/search/url/{}'.format(image_url)),
					Button.url('SauseNao', url='https://saucenao.com/search.php?db=999&dbmaski=32768&url={}'.format(image_url))
				],
				[
					Button.url('TinEye', url='https://tineye.com/search?url={}'.format(image_url))
				]
			])

			await client.send_file(entity=event.chat, file=message.media, buttons=buttons, reply_to=event.message)
		else:
			image_url = body.split('https://ascii2d.net/search/url/')[1].split('">')[0]
			doc = pq(body)
			buttons = [[Button.url('iqdb', url='https://iqdb.org/?url={}'.format(image_url))]]

			for match in doc('#pages table')[1:]:
				match_type = doc(match).find('tr').eq(0).text()
				match_source = doc(match).find('tr').eq(2).text()
				match_dims = doc(match).find('tr').eq(3).text()
				match_similarity = doc(match).find('tr').eq(4).text().split('%')[0]
				match_dims = doc(match).find('tr').eq(3).text()
				match_url = re.sub('^//', 'https://', doc(match).find('a').attr('href'))

				if match_type in {'Best match', 'Additional match'}:
					if match_source == 'Danbooru Gelbooru':
						gelbooru_url = re.sub('^//', 'https://', doc(match).find('a').eq(1).attr('href'))
						buttons.append([
							Button.url('Danbooru ({}%)'.format(match_similarity), url=match_url),
							Button.url('Gelbooru', url=gelbooru_url)
						])
					else:
						buttons.append([Button.url('{} ({}%)'.format(match_source, match_similarity), url=match_url)])

			await client.send_file(entity=event.chat, file=message.media, buttons=buttons, reply_to=event.message)

		if message.grouped_id and groups[message.grouped_id]:
			groups[message.grouped_id] -= 1
			if groups[message.grouped_id] == 0:
				await group_replies[message.grouped_id].delete()
			else:
				await group_replies[message.grouped_id].edit("Processing... {} queued".format(groups[message.grouped_id]))
		if processing_msg:
			await processing_msg.delete()
		await remove(file)
