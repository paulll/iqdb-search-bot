from pathlib import Path
import aiohttp
import asyncio
import uuid
import re


from aiofiles.os import remove
from os.path import normpath
from pyquery import PyQuery as pq
from telethon import events, functions, Button
from telethon.tl.types import MessageMediaPhoto
from .client import client

IQDB_HOST = 'https://iqdb.org/'
IQDB_MARKER_ERROR = '<!-- Failed...'
IQDB_MARKER_NO_RESULTS = 'No relevant matches'

session = aiohttp.ClientSession()



async def upload(path):
    file_id = 'iqdb/' + str(uuid.uuid4()) + Path(path).suffix
    headers = {'Content-Type': 'image/jpeg'}
    seaweed_response_raw = await session.put(f'http://filer-service.seaweed/{file_id}?ttl=30m', 
                                             data=open(path, 'rb'), 
                                             headers=headers)
    seaweed_response = await seaweed_response_raw.json()

    print(f'seaweed uploaded to https://blob.paulll.cc/${file_id} : {seaweed_response}')
    return f'https://blob.paulll.cc/${file_id}'



def build_stub_buttons(image_url):
    return client.build_reply_markup([
        [
            Button.url('Google', url='https://lens.google.com/uploadbyurl?url={}'.format(image_url)),
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


async def request_iqdb(path):
    """
            Total shit
            returns:
                    1) str if error (with error desc)
                    2) None if not found
                    3) buttons if found
    """
    form = (
        ('file', open(path, 'rb')),
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
    return body


async def send_ipfs_stub(context, event, path):
    url = await upload(path)
    context['url'] = url
    if context['done'] == False:
        buttons = build_stub_buttons(url)
        context['buttons'] = buttons
        await context['message'].edit('Still searching..', buttons=buttons)


async def send_iqdb_resp(context, event, path):
    body = await request_iqdb(path)
    if IQDB_MARKER_ERROR in body:
        await context['message'].edit('', buttons=context['buttons'])
        return None
    elif not 'https://ascii2d.net/search/url/' in body:
        print(' --- layout changed, could not parse --- ')
        print(body)
        await context['message'].edit('', buttons=context['buttons'])
        return None
    elif IQDB_MARKER_NO_RESULTS in body:
        await context['message'].edit('', buttons=context['buttons'])
        return None
    else:
        context['done'] = True
        if 'url' in context:
            image_url = context['url']
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
        await context['message'].edit('', buttons=buttons)


@client.on(events.NewMessage)
async def handler(event):
    """
    message -> send iqdb ->      build keyboard    -> (send / replace existing)
                    v            ^opt                       ^
                    -> send ipfs -> build keyboard -> send -| -x

    """
    message = event.message
    if message.media and isinstance(message.media, MessageMediaPhoto):
        file, message = await asyncio.gather(
            message.download_media(file="/dev/shm"),
            client.send_file(entity=event.chat, caption='Searching...', file=message.media, reply_to=event.message)
        )
        context = {
            'done': False,
            'message': message,
            'buttons': []
        }
        try:
            await asyncio.wait([
                send_ipfs_stub(context, event, file),
                send_iqdb_resp(context, event, file)
            ], return_when=asyncio.ALL_COMPLETED)
        finally:
            await remove(file)
