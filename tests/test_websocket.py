import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from pytrading.connectivity.http import AsyncClient
from pytrading.connectivity.websocket import ReconnectingWebsocket, KeepAliveWebsocket, \
    WebsocketManager, UnableToConnect, WSListenerState


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_reconnecting_websocket_connect_success(event_loop):
    mock_ws_connect = AsyncMock(return_value=AsyncMock())
    with patch('websockets.connect', mock_ws_connect):
        ws = ReconnectingWebsocket(url="ws://test.url", path="test_path", loop=event_loop)
        await ws.connect()
        assert ws.ws_state == WSListenerState.STREAMING
        assert ws._reconnects == 0
        mock_ws_connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_reconnecting_websocket_connect_failure(event_loop):
    mock_ws_connect = AsyncMock(side_effect=Exception("Connection failed"))
    with patch('websockets.connect', mock_ws_connect):
        ws = ReconnectingWebsocket(url="ws://test.url", path="test_path", loop=event_loop)
        with pytest.raises(UnableToConnect):
            await ws.connect()
        assert ws.ws_state == WSListenerState.RECONNECTING
        assert ws._reconnects == 1


@pytest.mark.asyncio
async def test_reconnecting_websocket_recv(event_loop):
    mock_ws_recv = AsyncMock(return_value='{"test": "message"}')
    mock_queue_get = AsyncMock(return_value='{"test": "message"}')
    with patch('websockets.connect', AsyncMock(return_value=AsyncMock(recv=mock_ws_recv))):
        ws = ReconnectingWebsocket(url="ws://test.url", path="test_path", loop=event_loop)
        await ws.connect()
        with patch.object(ws._queue, 'get', mock_queue_get):
            message = await ws.recv()
            assert message == {"test": "message"}


@pytest.mark.asyncio
async def test_reconnecting_websocket_reconnect(event_loop):
    mock_ws_connect = AsyncMock(side_effect=[Exception("Connection failed"), AsyncMock()])
    with patch('websockets.connect', mock_ws_connect):
        ws = ReconnectingWebsocket(url="ws://test.url", path="test_path", loop=event_loop)
        await ws.connect()
        assert ws._reconnects == 1
        await ws.connect()
        assert ws.ws_state == WSListenerState.STREAMING
        assert ws._reconnects == 0


@pytest.mark.asyncio
async def test_keepalive_websocket_keepalive(event_loop):
    mock_get_listen_key = AsyncMock(return_value="new_listen_key")
    with patch('websockets.connect', AsyncMock(return_value=AsyncMock())):
        client = AsyncClient()
        ws = KeepAliveWebsocket(client, url="ws://test.url", keepalive_type="test", loop=event_loop)
        ws._get_listen_key = mock_get_listen_key
        await ws.connect()
        await ws._keepalive_socket()
        assert ws._path == "new_listen_key"


@pytest.mark.asyncio
async def test_websocket_manager(event_loop):
    mock_ws = AsyncMock(spec=ReconnectingWebsocket)
    with patch('your_module.ReconnectingWebsocket', mock_ws):
        client = AsyncClient()
        manager = WebsocketManager(client, loop=event_loop)
        socket = manager._get_socket(path="test_path")
        assert socket in manager._conns.values()
        await manager._exit_socket("test_path")
        assert socket not in manager._conns.values()
