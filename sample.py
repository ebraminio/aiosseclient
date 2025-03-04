#!/usr/bin/env python3
"""Asynchronous Server Side Events (SSE) Client"""
import asyncio
import json
import aiohttp
from aiosseclient import aiosseclient

wikis = {}

# count: int = 0


async def fetch(session, d, url):
    """Fetch a url"""
    try:
        resp = await session.get(url)
        doc = await resp.text()
        d['content'] = doc
        with open('stream.json', 'a', encoding='utf8') as stream:
            json.dump(d, stream)
            stream.write('\n')
        return 'ok'

    except TimeoutError as e:
        print(e)
        return await fetch(session, d, url)


async def read_stream(session):
    """Main loop"""
    try:
        async for event in aiosseclient('https://stream.wikimedia.org/v2/stream/recentchange'):
            d = json.loads(event.data)

            w = d['wiki']
            if 'revision' in d:
                _id = d['revision'].get('old')
            else:
                continue

            if _id is None:
                continue

            if w not in wikis:
                wikis[w] = {'min': _id, 'max': _id, 'count': 1}

            if wikis[w]['min'] > _id:
                wikis[w]['min'] = _id

                # if wikis[w]['max'] < _id:
                #   wikis[w]['max'] = _id
                wikis[w]['count'] = wikis[w]['count'] + 1
                # pprint.pprint([w, wikis[w]])
                # pprint.pprint(d)

                server_script_path = d['server_script_path']
                server_url = d['server_url']

                url = server_url + server_script_path + f'/index.php?oldid={str(_id)}&action=raw'
                status = await fetch(session, d, url)
                print('status', status)
    except TimeoutError as e:
        print(e)
        return await read_stream(session)


async def main():
    """Main"""
    async with aiohttp.ClientSession() as session:
        never = await read_stream(session)
        print(never)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
