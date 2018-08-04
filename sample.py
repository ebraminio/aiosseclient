import asyncio
import aiohttp
from aiosseclient import aiosseclient
import pprint
import json
import collections
#c = Counter()
wikis = {}


# async def get_page(url):
#     response = yield from aiohttp.request(
#         'GET', url
#     )
#     return response


async def main():
    async for event in aiosseclient('https://stream.wikimedia.org/v2/stream/recentchange'):
        d = json.loads(event.data)

        w = d['wiki']
        if 'revision' in d:
            _id = d['revision']['old']
        else:
            continue
        
        if _id is None :
            continue
        
        if w not in wikis:
            wikis [w] = {'min': _id, 'max' : _id , 'count': 1}
       
        if wikis [w]['min'] > _id :
            wikis [w]['min']= _id
            
            #if wikis [w]['max'] < _id :
            # wikis [w]['max']= _id
            wikis [w]['count']= wikis [w]['count'] +1
            #pprint.pprint([w,wikis [w]])
            #pprint.pprint(d)

            server_script_path = d['server_script_path']
            server_url = d['server_url']

            url = server_url + server_script_path + '/index.php?oldid='+  str(_id) + '&action=raw'
            
            async with aiohttp.ClientSession() as session:
                response = await session.get(url)
                async for line in response.content:
                    line = line.decode('utf8')
                    print (url, line)
                        
            #print (get_page(url))


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
