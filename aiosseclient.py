import re
import aiohttp
import warnings

async def aiosseclient(url, last_id=None, **kwargs):
    if 'headers' not in kwargs:
        kwargs['headers'] = {}

    # The SSE spec requires making requests with Cache-Control: nocache
    kwargs['headers']['Cache-Control'] = 'no-cache'

    # The 'Accept' header is not required, but explicit > implicit
    kwargs['headers']['Accept'] = 'text/event-stream'
    
    if last_id:
        kwargs['headers']['Last-Event-ID'] = last_id
    
    # Override default timeout of 5 minutes
    timeout = aiohttp.ClientTimeout(total=None, connect=None,
                      sock_connect=None, sock_read=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        response = await session.get(url, **kwargs)
        lines = []
        async for line in response.content:
            line = line.decode('utf8')

            if line == '\n' or line == '\r' or line == '\r\n':
                if lines[0] == ':ok\n':
                    lines = []
                    continue

                yield Event.parse(''.join(lines))
                lines = []
            else:
                lines.append(line)


# Below code is directly brought from https://github.com/btubbs/sseclient/blob/db38dc6/sseclient.py#L101-L163
# Also some bits of aiosseclient() are also brought from the same file
class Event(object):

    sse_line_pattern = re.compile('(?P<name>[^:]*):?( ?(?P<value>.*))?')

    def __init__(self, data='', event='message', id=None, retry=None):
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry


    def dump(self):
        lines = []
        if self.id:
            lines.append('id: %s' % self.id)

        # Only include an event line if it's not the default already.
        if self.event != 'message':
            lines.append('event: %s' % self.event)

        if self.retry:
            lines.append('retry: %s' % self.retry)

        lines.extend('data: %s' % d for d in self.data.split('\n'))
        return '\n'.join(lines) + '\n\n'

    def encode(self):
        return self.dump().encode('utf-8')

        
    @classmethod
    def parse(cls, raw):
        """
        Given a possibly-multiline string representing an SSE message, parse it
        and return a Event object.
        """
        msg = cls()
        for line in raw.splitlines():
            m = cls.sse_line_pattern.match(line)
            if m is None:
                # Malformed line.  Discard but warn.
                warnings.warn('Invalid SSE line: "%s"' % line, SyntaxWarning)
                continue

            name = m.group('name')
            if name == '':
                # line began with a ":", so is a comment.  Ignore
                continue
            value = m.group('value')

            if name == 'data':
                # If we already have some data, then join to it with a newline.
                # Else this is it.
                if msg.data:
                    msg.data = '%s\n%s' % (msg.data, value)
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
    
