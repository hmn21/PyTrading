import asyncio
import unittest
from unittest.mock import patch

from pytrading.network.tcp import TCPServer, TCPClient, ServerProtocol, \
    ClientProtocol


class TestTCPAsyncServerClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    def setUp(self):
        self.server = TCPServer('127.0.0.1', 9999, ServerProtocol, loop=self.loop)
        self.client = TCPClient('127.0.0.1', 9999, ClientProtocol, loop=self.loop)
        self.server_task = self.loop.create_task(self.server.run())

    def tearDown(self):
        self.server_task.cancel()
        self.loop.run_until_complete(self.server_task)

    async def client_run(self, message):
        on_con_lost = self.loop.create_future()
        transport, protocol = await self.loop.create_connection(
            lambda: ClientProtocol(message, on_con_lost),
            self.client.host, self.client.port
        )
        try:
            await on_con_lost
        finally:
            transport.close()

    def test_server_client_connection_and_data_exchange(self):
        message = "Hello World!"
        with patch.object(ServerProtocol, 'connection_made') as mock_conn_made, \
                patch.object(ServerProtocol, 'data_received') as mock_data_received, \
                patch.object(ClientProtocol, 'data_received') as mock_client_data_received:
            self.loop.run_until_complete(self.client_run(message))

            mock_conn_made.assert_called_once()
            mock_data_received.assert_called_once_with(message.encode())
            mock_client_data_received.assert_called_once_with(message.encode())


if __name__ == '__main__':
    unittest.main()
