import time
from multiprocessing import Process

from loguru import logger
from utils.register_device import agent_loop


class PairingAgent:
    def __init__(self, iface, target_addr):
        self.iface = iface
        self.target_addr = target_addr
        dev_name = "dev_%s" % target_addr.upper().replace(":", "_")
        self.target_path = "/org/bluez/%s/%s" % (iface, dev_name)

    def __enter__(self):
        try:
            logger.debug("Starting agent process...")
            self.agent = Process(target=agent_loop, args=(self.target_path,))
            self.agent.start()
            time.sleep(0.25)
            logger.debug("Agent process started.")
            return self
        except Exception as e:
            logger.error(f"Error starting agent process: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            logger.debug("Terminating agent process...")
            self.agent.kill()
            time.sleep(2)
            logger.debug("Agent process terminated.")
        except Exception as e:
            logger.error(f"Error terminating agent process: {e}")
            raise
