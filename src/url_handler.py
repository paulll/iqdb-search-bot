import aiohttp
import asyncio
import re
import aiofiles

from os.path import normpath
from pyquery import PyQuery as pq
from telethon import events, functions, Button
from telethon.tl.types import MessageEntityTextUrl, MessageEntityUrl
from .client import client
from urllib.parse import urlencode

IQDB_HOST = 'https://iqdb.org/?'
IQDB_MARKER_ERROR = '<!-- Failed...'
IQDB_MARKER_NO_RESULTS = 'No relevant matches'

session = aiohttp.ClientSession()


@client.on(events.NewMessage)
async def handler(event):
	message = event.message
	print(message)
	print('--------------------')
	urls = set()

	if message.entities:
		for entity in message.entities:
			if isinstance(entity, MessageEntityUrl):
				urls.add(message.message[entity.offset: entity.offset+entity.length])
			if isinstance(entity, MessageEntityTextUrl):
				urls.add(entity.url)

	queued = len(urls)
	process = None
	if queued > 1:
		process = await message.reply("Processing... {} queued".format(queued))
	if queued == 1:
		process = await message.reply("Processing...")
	responces = await asyncio.gather(*[session.get(IQDB_HOST + urlencode({'url': url})) for url in urls])

	for resp in responces:
		body = await resp.text()
		url = resp.url.query['url']

		if IQDB_MARKER_ERROR in body:
			await message.reply('URL {} seems invalid'.format(url))
		elif not 'https://ascii2d.net/search/url/' in body:
			print(' --- unknown shit --- ')
			print(body)
			await message.reply('Something went wrong with {}'.format(url))
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
					Button.url('TinEye', url='https://tineye.com/search?url={}'.format(image_url)),
					Button.url('iqdb', url='https://iqdb.org1/?url={}'.format(image_url))
				]
			])
			await client.send_file(entity=event.chat, file=image_url, buttons=buttons, reply_to=message)
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

			await client.send_file(entity=event.chat, file=image_url, buttons=buttons, reply_to=message)

		queued -= 1
		if queued:
			await process.edit("Processing... {} queued".format(queued))
		else:
			await process.delete()
