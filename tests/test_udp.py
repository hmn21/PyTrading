import asyncio
import unittest
from unittest.mock import patch, MagicMock

from pytrading.connectivity.udp import UDPClient, UDPServer, ServerProtocol, ClientProtocol


class TestUDPClientServer(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        self.loop.close()

    @patch('builtins.print')
    def test_server_receives_and_sends_datagram(self, mock_print):
        async def test_case():
            server = UDPServer('127.0.0.1', 9999, ServerProtocol, loop=self.loop)
            server_task = self.loop.create_task(server.run())

            client = UDPClient('127.0.0.1', 9999, ClientProtocol, loop=self.loop)
            client_task = self.loop.create_task(client.run())

            await asyncio.sleep(1)  # Allow some time for datagram to be sent and received

            server_task.cancel()
            client_task.cancel()

        self.loop.run_until_complete(test_case())

        mock_print.assert_any_call('Received %r from %s', 'Hello World!', ('127.0.0.1', 9999))
        mock_print.assert_any_call('Send %r to %s', 'Hello World!', ('127.0.0.1', 9999))
        mock_print.assert_any_call('Send:', 'Hello World!')
        mock_print.assert_any_call("Received:", 'Hello World!')
        mock_print.assert_any_call("Close the socket")
        mock_print.assert_any_call("Connection closed")

    @patch('builtins.print')
    def test_client_error_received(self, mock_print):
        async def test_case():
            server = UDPServer('127.0.0.1', 9999, ServerProtocol, loop=self.loop)
            server_task = self.loop.create_task(server.run())

            client = UDPClient('127.0.0.1', 9999, ClientProtocol, loop=self.loop)
            client_task = self.loop.create_task(client.run())

            # Simulate an error received by the client
            client.protocol.error_received = MagicMock()
            client.protocol.error_received('Simulated error')

            await asyncio.sleep(1)  # Allow some time for error to be processed

            server_task.cancel()
            client_task.cancel()

        self.loop.run_until_complete(test_case())

        mock_print.assert_called_with('Error received:', 'Simulated error')


if __name__ == '__main__':
    unittest.main()
