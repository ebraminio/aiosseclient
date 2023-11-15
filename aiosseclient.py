'''Asynchronous Server Side Events (SSE) Client'''
import re
import warnings
from typing import (
    List,
    Optional,
    AsyncGenerator,
    Final,
)
import aiohttp

# pylint: disable=too-many-arguments, dangerous-default-value, redefined-builtin

_SSE_LINE_PATTERN: Final[re.Pattern[str]] = re.compile('(?P<name>[^:]*):?( ?(?P<value>.*))?')


# Good parts of the below class is adopted from:
#   https://github.com/btubbs/sseclient/blob/db38dc6/sseclient.py
class Event:
    '''The object created as the result of received events'''
    data: str
    event: str
    id: Optional[str]
    retry: Optional[bool]

    def __init__(
        self,
        data: str = '',
        event: str = 'message',
        id: Optional[str] = None,
        retry: Optional[bool] = None
    ):
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry

    def dump(self) -> str:
        '''Serialize the event object to a string'''
        lines = []
        if self.id:
            lines.append(f'id: {self.id}')

        # Only include an event line if it's not the default already.
        if self.event != 'message':
            lines.append(f'event: {self.event}')

        if self.retry:
            lines.append(f'retry: {self.retry}')

        lines.extend(f'data: {d}' for d in self.data.split('\n'))
        return '\n'.join(lines) + '\n\n'

    def encode(self) -> bytes:
        '''Serialize the event object to a bytes object'''
        return self.dump().encode('utf-8')

    @classmethod
    def parse(cls, raw):
        '''
        Given a possibly-multiline string representing an SSE message, parse it
        and return a Event object.
        '''
        msg = cls()
        for line in raw.splitlines():
            m = _SSE_LINE_PATTERN.match(line)
            if m is None:
                # Malformed line.  Discard but warn.
                warnings.warn('Invalid SSE line: "{line}"', SyntaxWarning)
                continue

            name = m.group('name')
            if name == '':
                # line began with a ':', so is a comment.  Ignore
                continue
            value = m.group('value')

            if name == 'data':
                # If we already have some data, then join to it with a newline.
                # Else this is it.
                if msg.data:
                    msg.data = f'{msg.data}\n{value}'
                else:
                    msg.data = value
            elif name == 'event':
                msg.event = value
            elif name == 'id':
                msg.id = value
            elif name == 'retry':
                msg.retry = int(value)

        return msg

    def __str__(self):
        return self.data


# pylint: disable=too-many-arguments, dangerous-default-value
async def aiosseclient(
    url: str,
    last_id: Optional[str] = None,
    valid_http_codes: List[int] = [200, 301, 307],
    exit_events: List[str] = [],
    timeout_total: Optional[float] = None,
    headers: Optional[dict[str, str]] = {},
) -> AsyncGenerator[Event, None]:
    '''Canonical API of the library'''
    # The SSE spec requires making requests with Cache-Control: nocache
    headers['Cache-Control'] = 'no-cache'

    # The 'Accept' header is not required, but explicit > implicit
    headers['Accept'] = 'text/event-stream'

    if last_id:
        headers['Last-Event-ID'] = last_id

    # Override default timeout of 5 minutes
    timeout = aiohttp.ClientTimeout(total=timeout_total, connect=None,
                                    sock_connect=None, sock_read=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            yield Event(f'session created: {session}', 'stream_telemetry')
            response = await session.get(url, headers=headers)
            if response.status not in valid_http_codes:
                yield Event(f'Invalid HTTP response.status: {response.status}', 'stream_failed')
                await session.close()
            lines = []
            async for line in response.content:
                line = line.decode('utf8')

                if line in {'\n', '\r', '\r\n'}:
                    if lines[0] == ':ok\n':
                        lines = []
                        continue

                    current_event = Event.parse(''.join(lines))
                    yield current_event
                    if current_event.event in exit_events:
                        await session.close()
                    lines = []
                else:
                    lines.append(line)
        except TimeoutError as sseerr:
            yield Event(f'TimeoutError: {sseerr}', 'session_failed')
            await session.close()
