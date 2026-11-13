"""Exercise protocol behavior against in-memory serial streams."""

import asyncio
import os
import sys
from collections.abc import AsyncIterator
from unittest.mock import patch

import pytest
from serialx import Parity, StopBits

from custom_components.ada_rs232.client import AdaClient


class AmpStream:
    """Small PAC simulator: S is silent and G returns hardware state."""

    def __init__(self) -> None:
        self.reader = asyncio.StreamReader()
        self.bits = "00000000"
        self.commands: list[bytes] = []
        self.command_sent = asyncio.Event()
        self.respond = True
        self.override = False
        self.closed = False
        self.write_error = False

    def write(self, data: bytes) -> None:
        if self.write_error:
            raise OSError("Cable removed")
        self.commands.append(data)
        self.command_sent.set()
        if data == b"G1\r\n" and self.respond:
            self.reader.feed_data(f"1={self.bits}\r\n".encode())
        elif data.startswith(b"S1=") and not self.override:
            self.bits = data[3:11].decode()

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        pass


@pytest.fixture
async def connection() -> AsyncIterator[tuple[AdaClient, AmpStream]]:
    stream = AmpStream()
    with patch(
        "custom_components.ada_rs232.client.open_serial_connection",
        return_value=(stream.reader, stream),
    ):
        client = AdaClient("/dev/test", timeout=0.2)
        yield client, stream
        await client.async_close()


async def test_serial_settings(connection) -> None:
    client, stream = connection
    with patch(
        "custom_components.ada_rs232.client.open_serial_connection",
        return_value=(stream.reader, stream),
    ) as open_port:
        assert await client.async_get_state() == (False,) * 8
        open_port.assert_awaited_once_with(
            "/dev/test",
            baudrate=19200,
            bytesize=8,
            parity=Parity.NONE,
            stopbits=StopBits.ONE,
            xonxoff=False,
            rtscts=False,
        )
    assert stream.commands == [b"G1\r\n"]


@pytest.mark.parametrize("ending", [b"\r", b"\n", b"\r\n", b""])
async def test_fragmented_feedback_and_noise(connection, ending) -> None:
    client, stream = connection
    stream.respond = False
    request = asyncio.create_task(client.async_get_state())
    await stream.command_sent.wait()
    stream.reader.feed_data(
        b"G1\r\nS1=11111111\r\n2=11111111\r\n1=1000000x\r\n1=100000000\r\n"
    )
    stream.reader.feed_data(b"1=101")
    await asyncio.sleep(0)
    stream.reader.feed_data(b"00101" + ending)
    assert await request == (True, False, True, False, False, True, False, True)


async def test_overlong_line_is_discarded_whole(connection) -> None:
    client, stream = connection
    stream.respond = False
    task = asyncio.create_task(client.async_get_state())
    await stream.command_sent.wait()
    stream.reader.feed_data(b"x" * 129 + b"1=11111111\n1=00000001\n")
    assert await task == (False,) * 7 + (True,)


async def test_simultaneous_writes_preserve_other_zones(connection) -> None:
    client, stream = connection
    stream.bits = "00100000"  # A zone enabled outside Home Assistant.
    await asyncio.gather(client.async_set_zone(1, True), client.async_set_zone(8, True))
    assert stream.bits == "10100001"
    assert stream.commands == [
        b"G1\r\n",
        b"S1=10100000\r\n",
        b"G1\r\n",
        b"G1\r\n",
        b"S1=10100001\r\n",
        b"G1\r\n",
    ]


async def test_hardware_override_is_authoritative(connection) -> None:
    client, stream = connection
    stream.override = True
    assert await client.async_set_zone(1, True) == (False,) * 8
    assert client.state == (False,) * 8


async def test_timeout_closes_then_next_poll_reconnects(connection) -> None:
    client, stream = connection
    stream.respond = False
    with pytest.raises(TimeoutError):
        await client.async_set_zone(1, True)
    assert stream.commands == [b"G1\r\n"]  # Never write unknown zone states.
    assert stream.closed
    assert client.state is None
    fresh = AmpStream()
    with patch(
        "custom_components.ada_rs232.client.open_serial_connection",
        return_value=(fresh.reader, fresh),
    ):
        assert await client.async_get_state() == (False,) * 8


async def test_eof_fails_pending_query(connection) -> None:
    client, stream = connection
    stream.respond = False
    task = asyncio.create_task(client.async_get_state())
    await stream.command_sent.wait()
    stream.reader.feed_eof()
    with pytest.raises(ConnectionError):
        await task
    assert stream.closed
    assert client.state is None


async def test_cancelled_query_releases_reader(connection) -> None:
    client, stream = connection
    stream.respond = False
    task = asyncio.create_task(client.async_get_state())
    await stream.command_sent.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert stream.closed
    assert client._reader_task is None


async def test_write_error_invalidates_state(connection) -> None:
    client, stream = connection
    await client.async_get_state()
    stream.write_error = True
    with pytest.raises(OSError):
        await client.async_set_zone(1, True)
    assert client.state is None
    assert stream.closed


async def test_no_confirmation_after_write_never_replays_command(connection) -> None:
    client, stream = connection
    original_write = stream.write

    def drop_confirmation(data):
        original_write(data)
        if data.startswith(b"S1="):
            stream.respond = False

    with patch.object(stream, "write", side_effect=drop_confirmation):
        with pytest.raises(TimeoutError):
            await client.async_set_zone(1, True)
    assert stream.bits == "10000000"  # The write may have succeeded.
    assert client.state is None  # But unconfirmed state is never trusted.
    fresh = AmpStream()
    fresh.bits = stream.bits
    with patch(
        "custom_components.ada_rs232.client.open_serial_connection",
        return_value=(fresh.reader, fresh),
    ):
        assert await client.async_get_state() == (True,) + (False,) * 7
    assert fresh.commands == [b"G1\r\n"]


@pytest.mark.skipif(sys.platform == "win32", reason="Requires POSIX pseudo terminals")
async def test_real_serialx_transport_over_pty() -> None:
    """Exercise actual serialx opening, framing and closing, without hardware."""
    master, slave = os.openpty()
    client = AdaClient(os.ttyname(slave), timeout=1)
    try:
        request = asyncio.create_task(client.async_get_state())
        # A loop reader avoids blocking the event loop on the emulator's fd.
        command = asyncio.get_running_loop().create_future()
        loop = asyncio.get_running_loop()

        def receive_command():
            data = os.read(master, 128)
            if not command.done():
                command.set_result(data)
            loop.remove_reader(master)

        loop.add_reader(master, receive_command)
        try:
            async with asyncio.timeout(2):
                assert await command == b"G1\r\n"
                os.write(master, b"1=01000000\r\n")
                assert await request == (False, True) + (False,) * 6
        finally:
            loop.remove_reader(master)
            if not request.done():
                request.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await request
    finally:
        await client.async_close()
        os.close(master)
        os.close(slave)


async def test_subscription_and_unsubscribe(connection) -> None:
    client, stream = connection
    states = []
    unsubscribe = client.subscribe(states.append)
    await client.async_get_state()
    stream.reader.feed_data(b"1=10000000\n")
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert states[-1] == (True,) + (False,) * 7
    unsubscribe()
    count = len(states)
    await client.async_close()
    assert len(states) == count


@pytest.mark.parametrize("address", [0, 10, True])
def test_invalid_address(address) -> None:
    with pytest.raises(ValueError):
        AdaClient("test", address=address)


@pytest.mark.parametrize("zone", [0, 9, True])
async def test_invalid_zone(connection, zone) -> None:
    client, stream = connection
    with pytest.raises(ValueError):
        await client.async_set_zone(zone, True)
    assert not stream.commands
