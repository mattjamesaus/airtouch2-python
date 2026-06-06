import asyncio
import unittest
from unittest.mock import AsyncMock

from airtouch2.at2plus.At2PlusAircon import At2PlusAircon
from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcPower, AcSetMode
from airtouch2.protocol.at2plus.messages.AcStatus import AcStatus
from airtouch2.protocol.at2plus.messages.AcAbilityMessage import AcAbility, SetpointLimits


class FakeClient:
    def __init__(self):
        self.sent = []

    async def send(self, msg):
        self.sent.append(msg)


class TestAt2PlusAircon(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.status = AcStatus(
            id=1,
            power=AcPower.ON,
            mode=AcSetMode.COOL,
            fan_speed=AcFanSpeed.MEDIUM,
            set_point=22.0,
            temperature=22.5,
            turbo=False,
            bypass=False,
            spill=False,
            timer=False,
            error=0,
        )
        self.client = FakeClient()
        self.aircon = At2PlusAircon(self.status, self.client)

    async def test_power_and_control_messages_are_sent(self):
        await self.aircon.turn_off()
        await self.aircon.turn_on()
        await self.aircon.toggle()
        await self.aircon.set_mode(AcSetMode.HEAT)
        await self.aircon.set_fan_speed(AcFanSpeed.HIGH)
        await self.aircon.set_setpoint(24.5)

        self.assertEqual(len(self.client.sent), 6)

    async def test_is_on_reflects_power_state(self):
        self.assertTrue(self.aircon.is_on())
        self.aircon.status.power = AcPower.OFF
        self.assertFalse(self.aircon.is_on())

    async def test_callbacks_fire_on_status_update(self):
        results = []

        def callback():
            results.append(True)

        self.aircon.add_callback(callback)
        self.aircon._update_status(self.status)
        self.assertEqual(results, [True])

    async def test_wait_until_ready_resolves_when_ability_set(self):
        task = asyncio.create_task(self.aircon.wait_until_ready())
        await asyncio.sleep(0)
        self.aircon._set_ability(AcAbility(1, "Test", 0, 1, [AcSetMode.AUTO], [AcFanSpeed.AUTO], SetpointLimits(10, 30)))
        await task
