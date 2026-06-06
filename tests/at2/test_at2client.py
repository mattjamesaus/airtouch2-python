import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from airtouch2.at2.At2Client import At2Client
from airtouch2.protocol.at2.enums import ACMode, ACFanSpeed, ACBrand
from airtouch2.protocol.at2.messages.SystemInfo import AcInfo, GroupInfo


class TestAt2Client(unittest.IsolatedAsyncioTestCase):
    async def test_add_new_ac_and_group_callback_unsubscribe(self):
        client = At2Client("127.0.0.1", task_creator=lambda coro: None)

        ac_called = []
        group_called = []

        def ac_callback():
            ac_called.append(True)

        def group_callback():
            group_called.append(True)

        remove_ac = client.add_new_ac_callback(ac_callback)
        remove_group = client.add_new_group_callback(group_callback)

        self.assertIn(ac_callback, client._new_ac_callbacks)
        self.assertIn(group_callback, client._new_group_callbacks)

        remove_ac()
        remove_group()
        self.assertNotIn(ac_callback, client._new_ac_callbacks)
        self.assertNotIn(group_callback, client._new_group_callbacks)

    async def test_on_connect_sends_request_state(self):
        client = At2Client("127.0.0.1", task_creator=lambda coro: None)
        client._client = Mock()
        client._client.send = AsyncMock()

        await client._on_connect()
        client._client.send.assert_awaited_once()

    async def test_handle_one_message_stores_ac_and_group_entries(self):
        client = At2Client("127.0.0.1", task_creator=lambda coro: None)
        client._client = Mock()
        client._new_ac_callbacks = []
        client._new_group_callbacks = []

        ac_info = AcInfo(
            number=0,
            name="AC1",
            active=True,
            mode=ACMode.COOL,
            supported_fan_speeds=[ACFanSpeed.LOW],
            fan_speed=ACFanSpeed.LOW,
            set_temp=22,
            measured_temp=21,
            brand=ACBrand.DAIKIN,
            program=0,
            error=False,
            error_code=0,
            thermistor=True,
            turbo=False,
            safety=False,
            spill=False,
        )
        group_info = GroupInfo(name="Group1", number=1, active=True, damp=5, spill=False, turbo=False)
        system_info = SimpleNamespace(
            system_name="TEST",
            touchpad_temp=18,
            aircons_by_id={0: ac_info},
            groups_by_id={1: group_info},
        )

        client._read_response = AsyncMock(return_value=system_info)
        client.add_new_ac_callback(lambda: None)
        client.add_new_group_callback(lambda: None)

        await client._handle_one_message()
        self.assertEqual(client.system_name, "TEST")
        self.assertEqual(client.touchpad_temp, 18)
        self.assertIn(0, client.aircons_by_id)
        self.assertIn(1, client.groups_by_id)
