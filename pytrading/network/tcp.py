import asyncio
from asyncio import Protocol
from typing import Type


class ServerProtocol(Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        print('Data received: {!r}'.format(message))

        print('Send: {!r}'.format(message))
        self.transport.write(data)

        print('Close the client socket')
        self.transport.close()


class TCPServer:
    def __init__(self, host: str, port: int, protocol: Type[Protocol], loop=None):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.loop = loop or asyncio.get_event_loop()

    async def run(self):
        server = await self.loop.create_server(
            self.protocol, '127.0.0.1', 9999
        )

        async with server:
            await server.serve_forever()


class ClientProtocol(Protocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost

    def connection_made(self, transport):
        transport.write(self.message.encode())
        print('Data sent: {!r}'.format(self.message))

    def data_received(self, data):
        print('Data received: {!r}'.format(data.decode()))

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.on_con_lost.set_result(True)


class TCPClient:
    def __init__(self, host: str, port: int, protocol: Type[ClientProtocol], loop=None):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.loop = loop or asyncio.get_event_loop()

    async def run(self):
        on_con_lost = self.loop.create_future()
        message = "Hello World!"

        transport, protocol = await self.loop.create_connection(
            lambda: self.protocol(message, on_con_lost),
            self.host, self.port
        )
        try:
            await on_con_lost
        finally:
            transport.close()
