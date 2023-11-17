'''A simple smoke test'''
import json
import pytest

from aiosseclient import aiosseclient

@pytest.mark.asyncio
async def test_basic_usage():
    '''Test basic usage.'''
    messages = []
    async for event in aiosseclient('https://stream.wikimedia.org/v2/stream/recentchange'):
        if len(messages) > 1:
            break
        messages.append(event)

    assert messages[0].event == 'message'
    assert messages[1].event == 'message'
    data_0 = json.loads(messages[0].data)
    data_1 = json.loads(messages[1].data)
    assert data_0['meta']['id'] != data_1['meta']['id']
