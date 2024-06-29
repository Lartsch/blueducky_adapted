import subprocess
import time
from multiprocessing import Process

from loguru import logger

from .adapter import Adapter
from .agent import PairingAgent

__all__ = ['Adapter', 'PairingAgent', 'setup_bluetooth', 'troubleshoot_bluetooth', 'terminate_child_processes', 'setup_and_connect']

from L2CAP.exceptions import ConnectionFailureException
from utils.menu_functions import run
from utils.register_device import register_hid_profile

child_processes = []


def setup_bluetooth(target_address, adapter_id):
    restart_bluetooth_daemon()
    profile_proc = Process(target=register_hid_profile, args=(adapter_id, target_address))
    profile_proc.start()
    child_processes.append(profile_proc)
    adapter = Adapter(adapter_id)
    adapter.set_property("name", "Robot POC")
    adapter.set_property("class", 0x002540)
    adapter.power(True)
    return adapter


def initialize_pairing(agent_iface, target_address):
    try:
        with PairingAgent(agent_iface, target_address) as agent:
            logger.debug("Pairing agent initialized")
    except Exception as e:
        logger.error(f"Failed to initialize pairing agent: {e}")
        raise ConnectionFailureException("Pairing agent initialization failed")


def establish_connections(connection_manager):
    if not connection_manager.connect_all():
        raise ConnectionFailureException("Failed to connect to all required ports")


def setup_and_connect(connection_manager, target_address, adapter_id):
    connection_manager.create_connection(1)
    connection_manager.create_connection(17)
    connection_manager.create_connection(19)
    initialize_pairing(adapter_id, target_address)
    establish_connections(connection_manager)
    return connection_manager.clients[19]


def troubleshoot_bluetooth():
    try:
        subprocess.run(['bluetoothctl', '--version'], check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("[!] CRITICAL: bluetoothctl is not installed or not working properly.")
        return False
    return True


def restart_bluetooth_daemon():
    run(["sudo", "service", "bluetoothM", "restart"])
    time.sleep(0.5)


def terminate_child_processes():
    for proc in child_processes:
        if proc.is_alive():
            proc.terminate()
            proc.join()