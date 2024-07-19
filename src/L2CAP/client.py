import binascii
import time
from datetime import datetime

import bluetooth
from loguru import logger

from .exceptions import ConnectionFailureException, ReconnectionRequiredException
from utils.helper import KeyCodes, ModifierCodes


class L2CAPClient:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.connected = False
        self.sock = None

    def encode_keyboard_input(*args):
        keycodes = []
        flags = 0
        for a in args:
            if isinstance(a, KeyCodes):
                keycodes.append(a.value)
            elif isinstance(a, ModifierCodes):
                flags |= a.value
        assert (len(keycodes) <= 7)
        keycodes += [0] * (7 - len(keycodes))
        report = bytes([0xa1, 0x01, flags, 0x00] + keycodes)
        return report

    def close(self):
        if self.connected:
            self.sock.close()
        self.connected = False
        self.sock = None

    def reconnect(self):
        raise ReconnectionRequiredException("Reconnection required")

    def send(self, data):
        if not self.connected:
            logger.error("[TX] Not connected")
            self.reconnect()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logger.debug(f"[{timestamp}][TX-{self.port}] Attempting to send data: {binascii.hexlify(data).decode()}")
        try:
            self.attempt_send(data)
            logger.debug(f"[TX-{self.port}] Data sent successfully")
        except bluetooth.btcommon.BluetoothError as ex:
            logger.error(f"[TX-{self.port}] Bluetooth error: {ex}")
            self.reconnect()
            self.send(data)
        except Exception as ex:
            logger.error(f"[TX-{self.port}] Exception: {ex}")
            raise

    def attempt_send(self, data, timeout=0.5):
        start = time.time()
        while time.time() - start < timeout:
            try:
                self.sock.send(data)
                return
            except bluetooth.btcommon.BluetoothError as ex:
                if ex.errno != 11:
                    raise
                time.sleep(0.001)

    def recv(self, timeout=0):
        start = time.time()
        while True:
            raw = None
            if not self.connected or not self.sock:
                return None
            try:
                raw = self.sock.recv(64)
                if len(raw) == 0:
                    self.connected = False
                    return None
                logger.debug(f"[RX-{self.port}] Received data: {binascii.hexlify(raw).decode()}")
            except bluetooth.btcommon.BluetoothError as ex:
                if ex.errno != 11:
                    raise ex
                else:
                    if (time.time() - start) < timeout:
                        continue
            return raw

    def connect(self, timeout=None):
        logger.debug(f"Attempting to connect to {self.addr} on port {self.port}")
        logger.info("connecting to %s on port %d" % (self.addr, self.port))
        sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        sock.settimeout(timeout)
        try:
            sock.connect((self.addr, self.port))
            sock.setblocking(0)
            self.sock = sock
            error = False
            self.connected = True
            logger.debug("SUCCESS! connected on port %d" % self.port)
        except Exception as ex:
            error = True
            self.connected = False
            logger.error("ERROR connecting on port %d: %s" % (self.port, ex))
            raise ConnectionFailureException(f"Connection failure on port {self.port}")
        if error and self.port == 14:
            print(f"[!] CRITICAL ERROR: Attempted Connection to {self.addr} was denied.")
            return self.connected

        return self.connected

    def send_keyboard_report(self, *args) -> None:
        self.send(self.encode_keyboard_input(*args))

    def send_keypress(self, *args, delay: float = 0.0001) -> bool:
        if args:
            logger.debug(f"Attempting to send... {args}")
            self.send(self.encode_keyboard_input(*args))
            time.sleep(delay)
            self.send(self.encode_keyboard_input())
            time.sleep(delay)
        else:
            self.send(self.encode_keyboard_input())
        time.sleep(delay)
        return True