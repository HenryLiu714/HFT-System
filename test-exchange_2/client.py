import os
import socket
from dataclasses import dataclass
from typing import Optional, Tuple

from dotenv import load_dotenv


load_dotenv()


def _get_int_env(name: str) -> int:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required for tests")
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an int, got {value!r}") from exc


CLIENT_IN_PORT = _get_int_env("CLIENT_IN_PORT")
EXCHANGE_IN_PORT = _get_int_env("EXCHANGE_IN_PORT")


@dataclass
class UdpClient:
    """
    Simple UDP client that acts as the EXCHANGE side.

    - Sends requests to the HFT system's input port (CLIENT_IN_PORT)
    - Listens for responses on EXCHANGE_IN_PORT
    """

    host: str = "127.0.0.1"
    send_port: int = CLIENT_IN_PORT
    recv_port: int = EXCHANGE_IN_PORT
    timeout_sec: float = 1.0

    def __post_init__(self) -> None:
        # Socket for sending requests to the HFT system
        self._send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Socket for receiving responses from the HFT system
        self._recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._recv_sock.bind((self.host, self.recv_port))
        self._recv_sock.settimeout(self.timeout_sec)

    def send(self, msg: str) -> None:
        """Send a raw FIX string to the HFT system."""
        self._send_sock.sendto(msg.encode("utf-8"), (self.host, self.send_port))

    def receive(self) -> Optional[str]:
        """
        Receive a response from the HFT system.

        Returns the decoded string, or None if no response before timeout.
        """
        try:
            data, _addr = self._recv_sock.recvfrom(4096)
        except socket.timeout:
            return None
        return data.decode("utf-8", errors="replace")

    def send_and_receive(self, msg: str) -> Tuple[Optional[str], float]:
        """
        Convenience helper that sends a message and waits for a single response.

        Returns (response, rtt_seconds).
        If there is no response before timeout, response is None and rtt is the elapsed time.
        """
        import time

        start = time.perf_counter()
        self.send(msg)
        response = self.receive()
        end = time.perf_counter()
        return response, end - start

    def send_and_receive_times(self, msg: str) -> Tuple[Optional[str], int, int]:
        """
        Send a message and return (response, send_time_ns, recv_time_ns).

        Times are taken from time.perf_counter_ns() so that the caller can
        compute precise round-trip latency and construct detailed traces.
        """
        import time

        start_ns = time.perf_counter_ns()
        self.send(msg)
        response = self.receive()
        end_ns = time.perf_counter_ns()
        return response, start_ns, end_ns

    def close(self) -> None:
        self._send_sock.close()
        self._recv_sock.close()


