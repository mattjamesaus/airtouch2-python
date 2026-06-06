import asyncio
import errno
import unittest
from unittest.mock import AsyncMock, Mock, patch

from airtouch2.common.NetClient import NetClient


class DummyMessage:
    def __init__(self, payload: bytes):
        self._payload = payload

    def to_bytes(self) -> bytes:
        return self._payload


class FakeSocket:
    SO_KEEPALIVE = True
    TCP_KEEPIDLE = True
    TCP_KEEPINTVL = True
    TCP_KEEPCNT = True
    TCP_USER_TIMEOUT = True

    def __init__(self):
        self.options = []

    def setsockopt(self, level, optname, value):
        self.options.append((level, optname, value))


class TestNetClient(unittest.IsolatedAsyncioTestCase):
    async def test_connect_success_calls_on_connect(self):
        fake_socket = FakeSocket()
        reader = Mock()
        writer = Mock()
        writer.get_extra_info.return_value = fake_socket
        writer.drain = AsyncMock()
        writer.write = Mock()

        open_mock = AsyncMock(return_value=(reader, writer))
        with patch("airtouch2.common.NetClient.asyncio.open_connection", open_mock):
            on_connect = AsyncMock()
            client = NetClient("127.0.0.1", 1234, on_connect, AsyncMock(), task_creator=lambda coro: None)
            connected = await client.connect()

        self.assertTrue(connected)
        on_connect.assert_awaited_once()
        self.assertIs(client._reader, reader)
        self.assertIs(client._writer, writer)
        self.assertTrue(fake_socket.options)

    async def test_connect_returns_false_on_network_error(self):
        open_mock = AsyncMock(side_effect=OSError(errno.ECONNREFUSED, "refused"))
        with patch("airtouch2.common.NetClient.asyncio.open_connection", open_mock):
            client = NetClient("127.0.0.1", 1234, AsyncMock(), AsyncMock(), task_creator=lambda coro: None)
            result = await client.connect()

        self.assertFalse(result)

    async def test_send_requires_connected_writer(self):
        client = NetClient("127.0.0.1", 1234, AsyncMock(), AsyncMock(), task_creator=lambda coro: None)
        with self.assertRaises(RuntimeError):
            await client.send(DummyMessage(b"abc"))

    async def test_send_writes_bytes_and_drains(self):
        client = NetClient("127.0.0.1", 1234, AsyncMock(), AsyncMock(), task_creator=lambda coro: None)
        writer = Mock()
        writer.write = Mock()
        writer.drain = AsyncMock()
        client._writer = writer

        await client.send(DummyMessage(b"abc"))
        writer.write.assert_called_once_with(b"abc")
        writer.drain.assert_awaited_once()

    async def test_send_retries_on_drain_failure(self):
        client = NetClient("127.0.0.1", 1234, AsyncMock(), AsyncMock(), task_creator=lambda coro: None)
        writer = Mock()
        writer.write = Mock()
        writer.drain = AsyncMock(side_effect=[ConnectionResetError(), None])
        client._writer = writer
        client._try_reconnect = AsyncMock()

        await client.send(DummyMessage(b"abc"))

        self.assertEqual(writer.write.call_count, 2)
        writer.write.assert_any_call(b"abc")
        self.assertEqual(writer.drain.await_count, 2)
        client._try_reconnect.assert_awaited_once()

    async def test_send_resends_after_reconnect(self):
        client = NetClient("127.0.0.1", 1234, AsyncMock(), AsyncMock(), task_creator=lambda coro: None)
        writer = Mock()
        writer.write = Mock()
        writer.drain = AsyncMock(side_effect=[ConnectionResetError(), None])
        client._writer = writer
        client._try_reconnect = AsyncMock()

        await client.send(DummyMessage(b"abc"))

        self.assertEqual(writer.write.call_count, 2)
        writer.write.assert_any_call(b"abc")
        client._try_reconnect.assert_awaited_once()

    async def test_read_bytes_returns_data(self):
        client = NetClient("127.0.0.1", 1234, AsyncMock(), AsyncMock(), task_creator=lambda coro: None)
        reader = Mock()
        reader.readexactly = AsyncMock(return_value=b"ab")
        client._reader = reader

        result = await client.read_bytes(2)
        self.assertEqual(result, b"ab")

    async def test_read_bytes_incomplete_reconnects(self):
        client = NetClient("127.0.0.1", 1234, AsyncMock(), AsyncMock(), task_creator=lambda coro: None)
        reader = Mock()
        reader.readexactly = AsyncMock(side_effect=asyncio.IncompleteReadError(partial=b"a", expected=2))
        client._reader = reader
        client._try_reconnect = AsyncMock()

        result = await client.read_bytes(2)
        self.assertIsNone(result)
        client._try_reconnect.assert_awaited_once()

    async def test_try_reconnect_retries_until_success(self):
        client = NetClient("127.0.0.1", 1234, AsyncMock(), AsyncMock(), task_creator=lambda coro: None)
        client.connect = AsyncMock(side_effect=[False, False, True])
        with patch("airtouch2.common.NetClient.asyncio.sleep", AsyncMock()):
            await client._try_reconnect()

        self.assertEqual(client.connect.await_count, 3)
