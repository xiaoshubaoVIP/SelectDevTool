import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional


CMD_HEAD = 0x5A
PROTOCOL_SIZE_MIN = 4
PROTOCOL_START_NUM = 2
PROTOCOL_TIMESTAMP_BIT = 0x04


@dataclass
class ParsedFrame:
    timestamp: int
    payload: bytes
    raw: bytes


def crc8_high_first(data: bytes) -> int:
    crc = 0
    for byte_val in data:
        i = 0x80
        while i:
            if crc & 0x80:
                crc = ((crc * 2) & 0xFF) ^ 0x07
            else:
                crc = (crc * 2) & 0xFF

            if byte_val & i:
                crc ^= 0x07
            i //= 2
    return crc & 0xFF


class FrameParser:
    def __init__(self) -> None:
        self._cache = bytearray()

    def feed(self, data: bytes, fallback_timestamp: Optional[int] = None) -> List[ParsedFrame]:
        self._cache.extend(data)
        frames: List[ParsedFrame] = []

        while len(self._cache) >= PROTOCOL_SIZE_MIN:
            if self._cache[0] != CMD_HEAD:
                del self._cache[0]
                continue

            cmd_len = self._cache[1]
            frame_len = cmd_len + PROTOCOL_START_NUM
            if cmd_len < 2:
                del self._cache[0]
                continue
            if frame_len > len(self._cache):
                break

            raw = bytes(self._cache[:frame_len])
            message = bytearray(self._cache[PROTOCOL_START_NUM:frame_len])
            if crc8_high_first(bytes(message)) != 0:
                del self._cache[0]
                continue

            timestamp = fallback_timestamp or int(datetime.now().timestamp())
            control = message.pop(0)

            if control & PROTOCOL_TIMESTAMP_BIT and len(message) >= 5:
                timestamp = (
                    message[0]
                    | (message[1] << 8)
                    | (message[2] << 16)
                    | (message[3] << 24)
                )
                del message[:4]

            if message:
                message.pop()

            frames.append(ParsedFrame(timestamp=timestamp, payload=bytes(message), raw=raw))
            del self._cache[:frame_len]

        return frames


def bytes_to_hex(data: bytes) -> str:
    return " ".join(f"{item:02X}" for item in data)


def hex_to_bytes(hex_string: str) -> bytes:
    values = re.findall(r"(?i)\b[0-9a-f]{2}\b", hex_string)
    return bytes(int(value, 16) for value in values)


def extract_log_timestamp(line: str) -> Optional[int]:
    match = re.search(r"\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}", line)
    if not match:
        return None
    try:
        return int(datetime.strptime(match.group(), "%Y-%m-%d %H:%M:%S").timestamp())
    except ValueError:
        return None


def extract_receive_hex(line: str) -> Optional[str]:
    if "Receive:" not in line:
        return None

    quoted = re.search(r'Receive:\s*"([^"]+)"', line)
    if quoted:
        return quoted.group(1)

    return line.split("Receive:", 1)[1]


def iter_log_frames(lines: Iterable[str]) -> Iterable[ParsedFrame]:
    parser = FrameParser()
    for line in lines:
        hex_string = extract_receive_hex(line)
        if not hex_string:
            continue
        timestamp = extract_log_timestamp(line)
        data = hex_to_bytes(hex_string)
        yield from parser.feed(data, timestamp)
