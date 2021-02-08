Asynchronous Server Side Events (SSE) Client 
========================

Similar to [sseclient](https://github.com/btubbs/sseclient) and [sseclient-py](https://github.com/mpetazzoni/sseclient), a tiny package for supporting Server Side Events (SSE) with py3.5 [asyncio](https://www.python.org/dev/peps/pep-3156/) and [aiohttp](http://aiohttp.readthedocs.io/en/stable/).

Install it with this: `pip3 install git+https://github.com/ebraminio/aiosseclient`

Sample code ([read more](https://wikitech.wikimedia.org/wiki/EventStreams)):
```python
import asyncio
import aiohttp
from aiosseclient import aiosseclient

async def main():
    async for event in aiosseclient('https://stream.wikimedia.org/v2/stream/recentchange'):
        print(event)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```