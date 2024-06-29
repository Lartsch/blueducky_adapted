import logging as log
import os
import re
import subprocess

import bluetooth
from art import tprint
from config import TITLE


def get_target_address():
    print(f"\n What is the target address? Leave blank and we will scan for you!")
    target_address = input(f"\n > ")

    if target_address == "":
        devices = scan_for_devices()
        if devices:
            if len(devices) == 1 and isinstance(devices[0], tuple) and len(devices[0]) == 2:
                confirm = input(f"\n Would you like to register this device:\n{devices[0][1]} {devices[0][0]}? (y/n) ").strip().lower()
                if confirm == 'y' or confirm == 'yes':
                    return devices[0][0]
                elif confirm != 'y' or 'yes':
                    return
            else:
                for idx, (addr, name) in enumerate(devices):
                    print(f"[{idx + 1}] Device Name: {name}, Address: {addr}")
                selection = int(input(f"\nSelect a device by number: ")) - 1
                if 0 <= selection < len(devices):
                    target_address = devices[selection][0]
                else:
                    print("\nInvalid selection. Exiting.")
                    return
        else:
            return
    elif not is_valid_mac_address(target_address):
        print("\nInvalid MAC address format. Please enter a valid MAC address.")
        return

    return target_address


def run(command):
    assert(isinstance(command, list))
    log.info("executing '%s'" % " ".join(command))
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result


def clear_screen():
    os.system('clear')


def save_devices_to_file(devices, filename='known_devices.txt'):
    with open(filename, 'w') as file:
        for addr, name in devices:
            file.write(f"{addr},{name}\n")


def scan_for_devices():
    main_menu()

    known_devices = load_known_devices()
    if known_devices:
        print(f"\nKnown devices: ")
        for idx, (addr, name) in enumerate(known_devices):
            print(f"{idx + 1}: Device Name: {name}, Address: {addr}")

        use_known_device = input(f"\nDo you want to use one of these known devices? (yes/no): ")
        if use_known_device.lower() == 'yes':
            device_choice = int(input(f"Enter the index number of the device to attack: "))
            return [known_devices[device_choice - 1]]

    print(f"\nAttempting to scan now...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True, lookup_class=True)
    device_list = []
    if len(nearby_devices) == 0:
        print(f"\n[+] No nearby devices found.")
    else:
        print("\nFound {} nearby device(s):".format(len(nearby_devices)))
        for idx, (addr, name, _) in enumerate(nearby_devices):
            device_list.append((addr, name))

    # Save the scanned devices only if they are not already in known devices
    new_devices = [device for device in device_list if device not in known_devices]
    if new_devices:
        known_devices += new_devices
        save_devices_to_file(known_devices)
        for idx, (addr, name) in enumerate(new_devices):
            print(f"{idx + 1}: Device Name: {name}, Address: {addr}")
    return device_list


def main_menu():
    clear_screen()
    tprint(TITLE, font='wetletter')
    print('Made by Information Security Club <3')


def is_valid_mac_address(mac_address):
    mac_address_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return mac_address_pattern.match(mac_address) is not None



def read_duckyscript(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return [line.strip() for line in file.readlines()]
    else:
        log.warning(f"File {filename} not found. Skipping DuckyScript.")



def load_known_devices(filename='known_devices.txt') -> list:
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return [tuple(line.strip().split(',')) for line in file]