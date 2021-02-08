#!/usr/bin/env python3
import asyncio
import aiohttp
from aiosseclient import aiosseclient
import pprint
import json

wikis = {}

ostream = open("stream.json", 'a')
count = 0

async def fetch(session, d, url):
    try:
        resp = await session.get(url)
        doc = await resp.text()
        d['content'] = doc
        json.dump(d, ostream)
        ostream.write('\n')
        return 'ok'

    except concurrent.futures._base.TimeoutError as e:
        print(e)
        return await fetch(session,d,  url)

async def read_stream(session):
    try:
        async for event in aiosseclient('https://stream.wikimedia.org/v2/stream/recentchange'):
            d = json.loads(event.data)

            w = d['wiki']
            if 'revision' in d:
                _id = d['revision']['old']
            else:
                continue

            if _id is None:
                continue

            if w not in wikis:
                wikis [w] = {'min': _id, 'max' : _id , 'count': 1}

            if wikis [w]['min'] > _id :
                wikis [w]['min'] = _id

                #if wikis [w]['max'] < _id:
                # wikis [w]['max'] = _id
                wikis [w]['count'] = wikis [w]['count'] +1
                #pprint.pprint([w, wikis[w]])
                #pprint.pprint(d)

                server_script_path = d['server_script_path']
                server_url = d['server_url']

                url = server_url + server_script_path + '/index.php?oldid=' + str(_id) + '&action=raw'
                status = await fetch(session, d, url)
                global count
                count = count + 1
                if count % 1000 == 0:
                    print(".")
    except Exception as e:
        print(e)
        return await read_stream(session)

async def main():
    async with aiohttp.ClientSession() as session:
        never = await read_stream(session)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
