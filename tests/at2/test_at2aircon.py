import asyncio
import unittest
from unittest.mock import AsyncMock

from airtouch2.at2.At2Aircon import At2Aircon
from airtouch2.protocol.at2.enums import ACFanSpeed, ACBrand, ACMode
from airtouch2.protocol.at2.messages.SystemInfo import AcInfo
from airtouch2.protocol.at2.messages import ChangeSetTemperature, SetFanSpeed, SetMode, ToggleAc


class FakeClient:
    def __init__(self):
        self.sent = []

    async def send(self, msg):
        self.sent.append(msg)


class TestAt2Aircon(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.info = AcInfo(
            number=0,
            name="TestAC",
            active=True,
            mode=ACMode.COOL,
            supported_fan_speeds=[ACFanSpeed.LOW, ACFanSpeed.MEDIUM],
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
        self.client = FakeClient()
        self.ac = At2Aircon(self.client, self.info)

    async def test_turn_on_and_off_send_toggle(self):
        await self.ac.turn_on()
        await self.ac.turn_off()

        self.assertEqual(len(self.client.sent), 2)
        self.assertIsInstance(self.client.sent[0], ToggleAc)
        self.assertIsInstance(self.client.sent[1], ToggleAc)

    async def test_set_mode_sends_set_mode(self):
        await self.ac.set_mode(ACMode.HEAT)
        self.assertIsInstance(self.client.sent[-1], SetMode)

    async def test_set_fan_speed_sends_set_fan_speed_when_supported(self):
        await self.ac.set_fan_speed(ACFanSpeed.MEDIUM)
        self.assertIsInstance(self.client.sent[-1], SetFanSpeed)

    async def test_set_fan_speed_ignores_unsupported_speed(self):
        await self.ac.set_fan_speed(ACFanSpeed.HIGH)
        self.assertEqual(self.client.sent, [])

    async def test_set_setpoint_sends_multiple_messages(self):
        await self.ac.set_set_temp(24)
        self.assertEqual(len(self.client.sent), 2)
        self.assertTrue(all(isinstance(msg, ChangeSetTemperature) for msg in self.client.sent))

    def test_update_notifies_callbacks(self):
        events = []

        def marker():
            events.append(True)

        remove = self.ac.add_callback(marker)
        self.ac.update(self.info)
        self.assertEqual(events, [True])

        remove()
        self.ac.update(self.info)
        self.assertEqual(events, [True])

    async def test_is_on_reflects_current_power(self):
        self.assertFalse(self.ac.is_on())
        self.ac.status.power = 1
        self.assertTrue(self.ac.is_on())
