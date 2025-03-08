"""Main module"""
from __future__ import annotations
import logging
from typing import (
    List,
    Optional,
    AsyncGenerator,
    Dict
)
import asyncio
import aiohttp

# pylint: disable=too-many-arguments, dangerous-default-value, redefined-builtin

_LOGGER = logging.getLogger(__name__)


# Good parts of the below class is adopted from:
#   https://github.com/btubbs/sseclient/blob/db38dc6/sseclient.py
class Event:
    """The object created as the result of received events"""
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
        """Serialize the event object to a string"""
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
        """Serialize the event object to a bytes object"""
        return self.dump().encode('utf-8')

    @classmethod
    def parse(cls, raw: str) -> Event:
        """
        Given a possibly-multiline string representing an SSE message, parse it
        and return an Event object.
        """
        msg = cls()
        for line in raw.splitlines():
            parts = line.split(':', 1)
            if len(parts) != 2:
                # Malformed line.  Discard but warn.
                _LOGGER.warning('Invalid SSE line: %s', line)
                continue

            name, value = parts
            if value.startswith(' '):
                value = value[1:]

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
                msg.retry = bool(value)

        return msg

    def __str__(self) -> str:
        return self.data


# noinspection PyDefaultArgument
# flake8: noqa: C901
# pylint: disable=too-many-arguments, dangerous-default-value
async def aiosseclient(
    url: str,
    last_id: Optional[str] = None,
    valid_http_codes: List[int] = [200, 301, 307],
    exit_events: List[str] = [],
    timeout_total: Optional[float] = None,
    headers: Optional[Dict[str, str]] = None,
    raise_for_status: bool = False,
) -> AsyncGenerator[Event, None]:
    """Canonical API of the library"""
    if headers is None:
        headers = {}
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
        response = None
        try:
            _LOGGER.info('Session created: %s', session)
            response = await session.get(url, headers=headers, raise_for_status=raise_for_status)
            if response.status not in valid_http_codes:
                _LOGGER.error('Invalid HTTP response.status: %s', response.status)
                await session.close()
            lines = []
            async for line in response.content:
                line = line.decode('utf8')

                if line in {'\n', '\r', '\r\n'}:
                    if not lines:
                        continue
                    current_event = Event.parse(''.join(lines))
                    yield current_event
                    if current_event.event in exit_events:
                        await session.close()
                    lines = []
                elif line.startswith(':'):
                    # Lines start with a ':' are comment, ignore them
                    pass
                else:
                    lines.append(line)
        except asyncio.TimeoutError as e:
            _LOGGER.error('TimeoutError: %s', e)
        finally:
            if response:
                response.close()
            if not session.closed:
                await session.close()
