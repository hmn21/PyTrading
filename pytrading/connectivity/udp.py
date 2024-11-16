import asyncio
from asyncio import DatagramProtocol
from typing import Type


class ServerProtocol(DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        print('Received %r from %s' % (message, addr))
        print('Send %r to %s' % (message, addr))
        self.transport.sendto(data, addr)


class UDPServer:
    def __init__(self, host: str, port: int, protocol: Type[DatagramProtocol], loop=None):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.loop = loop or asyncio.get_event_loop()

    async def run(self):
        transport, protocol = await self.loop.create_datagram_endpoint(
            self.protocol,
            local_addr=('127.0.0.1', 9999))

        try:
            await asyncio.sleep(3600)  # Serve for 1 hour.
        finally:
            transport.close()


class ClientProtocol(DatagramProtocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('Send:', self.message)
        self.transport.sendto(self.message.encode())

    def datagram_received(self, data, addr):
        print("Received:", data.decode())

        print("Close the socket")
        self.transport.close()

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")
        self.on_con_lost.set_result(True)


class UDPClient:
    def __init__(self, host: str, port: int, protocol: Type[ClientProtocol], loop=None):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.loop = loop or asyncio.get_event_loop()

    async def run(self):
        on_con_lost = self.loop.create_future()
        message = "Hello World!"

        transport, protocol = await self.loop.create_datagram_endpoint(
            lambda: self.protocol(message, on_con_lost),
            remote_addr=(self.host, self.port))
        try:
            await on_con_lost
        finally:
            transport.close()
