from __future__ import annotations
from dataclasses import dataclass

from airtouch2.common.Buffer import Buffer
from airtouch2.common.interfaces import Serializable
from airtouch2.protocol.at2plus.conversions import temperature_from_value
from airtouch2.protocol.at2plus.control_status_common import (
    CONTROL_STATUS_SUBHEADER_LENGTH,
    ControlStatusSubHeader,
    ControlStatusSubType,
    SubDataLength,
)
from airtouch2.protocol.at2plus.message_common import (
    AddressMsgType,
    Header,
    MessageType,
    add_checksum_message_buffer,
    prime_message_buffer,
)

AUX_SENSOR_STATUS_RECORD_LENGTH = 4


@dataclass
class AuxSensorStatus(Serializable):
    sensor_id: int
    associated_id: int | None
    temperature: float | None
    raw_temperature: int | None

    def to_bytes(self) -> bytes:
        raw_temperature = self.raw_temperature if self.raw_temperature is not None else 0x07FF
        associated_id = self.associated_id if self.associated_id is not None else 0xFF
        buffer = Buffer(AUX_SENSOR_STATUS_RECORD_LENGTH)
        buffer.append_bytes(bytes([
            self.sensor_id,
            associated_id,
        ]))
        buffer.append_bytes(raw_temperature.to_bytes(2, 'big'))
        return buffer.to_bytes()


class AuxSensorStatusMessage(Serializable):
    statuses: list[AuxSensorStatus]

    def __init__(self, statuses: list[AuxSensorStatus]):
        self.statuses = statuses

    @staticmethod
    def from_bytes(subdata: bytes) -> AuxSensorStatusMessage:
        if len(subdata) % AUX_SENSOR_STATUS_RECORD_LENGTH != 0:
            raise ValueError(
                f"Aux sensor status payload length must be a multiple of {AUX_SENSOR_STATUS_RECORD_LENGTH}, got {len(subdata)}")

        statuses: list[AuxSensorStatus] = []
        for offset in range(0, len(subdata), AUX_SENSOR_STATUS_RECORD_LENGTH):
            record = subdata[offset:offset + AUX_SENSOR_STATUS_RECORD_LENGTH]
            sensor_id = record[0]
            associated_id = None if record[1] == 0xFF else record[1]
            raw_temperature = int.from_bytes(record[2:4], 'big')
            temperature = temperature_from_value(raw_temperature)
            if raw_temperature == 0x07FF:
                temperature = None
            statuses.append(AuxSensorStatus(
                sensor_id,
                associated_id,
                temperature,
                raw_temperature,
            ))
        return AuxSensorStatusMessage(statuses)

    def to_bytes(self) -> bytes:
        subheader = ControlStatusSubHeader(
            ControlStatusSubType.AUX_SENSOR_STATUS,
            SubDataLength(0, len(self.statuses), AUX_SENSOR_STATUS_RECORD_LENGTH),
        )
        buffer = prime_message_buffer(
            Header(
                AddressMsgType.NORMAL,
                MessageType.CONTROL_STATUS,
                CONTROL_STATUS_SUBHEADER_LENGTH + subheader.subdata_length.total(),
            )
        )
        buffer.append(subheader)
        for status in self.statuses:
            buffer.append(status)
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
