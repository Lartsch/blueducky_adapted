from loguru import logger

from .client import L2CAPClient
from .exceptions import ConnectionFailureException


class L2CAPConnectionManager:
    def __init__(self, target_address):
        self.target_address = target_address
        self.clients = {}

    def create_connection(self, port):
        client = L2CAPClient(self.target_address, port)
        self.clients[port] = client
        return client

    def connect_all(self):
        try:
            return sum(client.connect() for client in self.clients.values())
        except ConnectionFailureException as e:
            logger.error(f"Connection failure: {e}")
            raise

    def close_all(self):
        for client in self.clients.values():
            client.close()