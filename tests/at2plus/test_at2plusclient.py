import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from airtouch2.at2plus.At2PlusClient import At2PlusClient
from airtouch2.protocol.at2plus.messages.AcAbilityMessage import AcAbility, AcAbilityMessage, SetpointLimits
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcMode, AcPower, GroupPower, AcSetPower, AcSetMode
from airtouch2.protocol.at2plus.extended_common import ExtendedMessageSubType, ExtendedSubHeader
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, Message, add_checksum_message_buffer, prime_message_buffer
from airtouch2.protocol.at2plus.messages.AcAbilityMessage import AcAbility, AcAbilityMessage, RequestAcAbilityMessage
from airtouch2.protocol.at2plus.messages.AcStatus import AcStatus, AcStatusMessage
from airtouch2.protocol.at2plus.messages.GroupStatus import GroupStatus, GroupStatusMessage
from airtouch2.protocol.at2plus.messages.GroupNames import RequestGroupNamesMessage
from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubHeader, ControlStatusSubType, SubDataLength
from airtouch2.common.Buffer import Buffer


class TestAt2PlusClient(unittest.IsolatedAsyncioTestCase):
    async def test_read_magic_skips_bytes_until_header(self):
        client = At2PlusClient("127.0.0.1", task_creator=lambda coro: None)
        client._client = Mock()
        client._client.read_bytes = AsyncMock(side_effect=[b"\x00", b"\x55", b"\x55"])

        magic = await client._read_magic()
        self.assertEqual(magic, bytes([0x55, 0x55]))

    async def test_read_header_parses_received_header(self):
        client = At2PlusClient("127.0.0.1", task_creator=lambda coro: None)
        header = Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, 4, _received=True)
        header_bytes = header.to_bytes()
        client._client = Mock()
        client._client.read_bytes = AsyncMock(side_effect=[b"\x55", b"\x55", header_bytes[2:]])

        read_header, raw_bytes = await client._read_header()
        self.assertEqual(read_header.type, MessageType.CONTROL_STATUS)
        self.assertEqual(raw_bytes, header_bytes)

    async def test_read_message_returns_message_when_checksum_is_valid(self):
        client = At2PlusClient("127.0.0.1", task_creator=lambda coro: None)
        status = AcStatus(1, AcPower.ON, AcMode.COOL, AcFanSpeed.MEDIUM, 22.0, 22.0, False, False, False, False, 0)
        subdata = AcStatusMessage([status]).to_bytes()[8:-2]
        header = Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, len(subdata), _received=True)
        buffer = prime_message_buffer(header)
        buffer.append_bytes(subdata)
        add_checksum_message_buffer(buffer)
        message_bytes = buffer.to_bytes()

        client._client = Mock()
        client._client.read_bytes = AsyncMock(side_effect=[
            b"\x55",
            b"\x55",
            bytes(message_bytes[2:8]),
            bytes(message_bytes[8:-2]),
            bytes(message_bytes[-2:])
        ])

        message = await client._read_message()
        self.assertEqual(message.header.data_length, len(message.data_buffer.to_bytes()))
        self.assertEqual(message.data_buffer.to_bytes(), message_bytes[8:-2])

    async def test_read_message_returns_none_on_bad_checksum(self):
        client = At2PlusClient("127.0.0.1", task_creator=lambda coro: None)
        status = AcStatus(1, AcPower.ON, AcMode.COOL, AcFanSpeed.MEDIUM, 22.0, 22.0, False, False, False, False, 0)
        subdata = AcStatusMessage([status]).to_bytes()[8:-2]
        header = Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, len(subdata), _received=True)
        buffer = prime_message_buffer(header)
        buffer.append_bytes(subdata)
        add_checksum_message_buffer(buffer)
        message_bytes = bytearray(buffer.to_bytes())
        message_bytes[-1] ^= 0xFF

        client._client = Mock()
        client._client.read_bytes = AsyncMock(side_effect=[
            b"\x55",
            b"\x55",
            bytes(message_bytes[2:8]),
            bytes(message_bytes[8:-2]),
            bytes(message_bytes[-2:])
        ])

        message = await client._read_message()
        self.assertIsNone(message)

    async def test_request_ac_ability_validates_single_ability(self):
        client = At2PlusClient("127.0.0.1", task_creator=lambda coro: None)
        client._client = Mock()
        client._client.send = AsyncMock()

        ability = AcAbility(1, "AC1", 0, 1, [AcSetMode.COOL], [AcFanSpeed.AUTO], SetpointLimits(10, 30))
        task = asyncio.create_task(client._request_ac_ability(1))
        await asyncio.sleep(0)
        client._dispatch_ability_message(AcAbilityMessage([ability]))

        result = await task
        self.assertEqual(result, ability)
        client._client.send.assert_awaited_once()

    async def test_request_ac_ability_rejects_mismatched_ac(self):
        client = At2PlusClient("127.0.0.1", task_creator=lambda coro: None)
        client._client = Mock()
        client._client.send = AsyncMock()

        ability = AcAbility(2, "AC2", 0, 1, [AcSetMode.COOL], [AcFanSpeed.AUTO], SetpointLimits(10, 30))
        task = asyncio.create_task(client._request_ac_ability(1, timeout=0.01))
        await asyncio.sleep(0)
        client._dispatch_ability_message(AcAbilityMessage([ability]))

        result = await task
        self.assertIsNone(result)
        client._client.send.assert_awaited_once()

    async def test_handle_group_name_updates_group_name(self):
        client = At2PlusClient("127.0.0.1", task_creator=lambda coro: None)
        fake_group = Mock()
        client.groups_by_id = {5: fake_group}
        client._client = Mock()

        buffer = Buffer(11)
        buffer.append_bytes(bytes([0xFF, ExtendedMessageSubType.GROUP_NAME]))
        buffer.append_bytes(bytes([5]) + b"Kitchen\x00")
        message = Message(Header(AddressMsgType.EXTENDED, MessageType.EXTENDED, 11, _received=True), buffer)

        client._read_message = AsyncMock(return_value=message)
        await client.handle_one_message()

        fake_group._update_name.assert_called_once_with("Kitchen")

    async def test_add_new_ac_and_group_callback_removed(self):
        client = At2PlusClient("127.0.0.1", task_creator=lambda coro: None)
        ac_events = []
        group_events = []

        remove_ac = client.add_new_ac_callback(lambda: ac_events.append(True))
        remove_group = client.add_new_group_callback(lambda: group_events.append(True))

        remove_ac()
        remove_group()

        self.assertEqual(ac_events, [])
        self.assertEqual(group_events, [])
