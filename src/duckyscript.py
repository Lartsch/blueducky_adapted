import time

from loguru import logger

from L2CAP.exceptions import ReconnectionRequiredException
from utils.helper import ModifierCodes, KeyCodes, char_to_key_code


def process_duckyscript(client, duckyscript, current_line=0, current_position=0):
    client.send_keypress('')
    time.sleep(0.5)

    shift_required_characters = "!@#$%^&*()_+{}|:\"<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    try:
        for line_number, line in enumerate(duckyscript):
            if line_number < current_line:
                continue

            if line_number == current_line and current_position > 0:
                line = line[current_position:]
            else:
                current_position = 0

            line = line.strip()
            logger.info(f"Processing {line}")
            if not line or line.startswith("REM"):
                current_line += 1
                continue
            if line.startswith("TAB"):
                client.send_keypress(KeyCodes.TAB)
            if line.startswith("PRIVATE_BROWSER"):
                report = bytes(
                    [0xa1, 0x01, ModifierCodes.CTRL.value | ModifierCodes.SHIFT.value, 0x00, KeyCodes.n.value, 0x00,
                     0x00, 0x00, 0x00, 0x00, 0x00])
                client.send(report)
                release_report = bytes([0xa1, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                client.send(release_report)
            if line.startswith("VOLUME_UP"):
                hid_report_gui_v = bytes.fromhex("a1010800190000000000")
                client.send(hid_report_gui_v)
                time.sleep(0.1)
                client.send_keypress(KeyCodes.TAB)
                hid_report_up = bytes.fromhex("a1010800195700000000")
                client.send(hid_report_up)
                time.sleep(0.1)
                hid_report_release = bytes.fromhex("a1010000000000000000")
                client.send(hid_report_release)
            if line.startswith("DELAY"):
                try:
                    delay_time = int(line.split()[1])
                    time.sleep(delay_time / 1000)
                except ValueError:
                    logger.error(f"Invalid DELAY format in line: {line}")
                except IndexError:
                    logger.error(f"DELAY command requires a time parameter in line: {line}")
                current_line += 1
                continue
            if line.startswith("STRING"):
                text = line[7:]
                for char_position, char in enumerate(text, start=1):
                    logger.info(f"Attempting to send letter: {char}")
                    try:
                        if char.isdigit():
                            key_code = getattr(KeyCodes, f"_{char}")
                            client.send_keypress(key_code)
                        elif char == " ":
                            client.send_keypress(KeyCodes.SPACE)
                        elif char == "[":
                            client.send_keypress(KeyCodes.LEFTBRACE)
                        elif char == "]":
                            client.send_keypress(KeyCodes.RIGHTBRACE)
                        elif char == ";":
                            client.send_keypress(KeyCodes.SEMICOLON)
                        elif char == "'":
                            client.send_keypress(KeyCodes.QUOTE)
                        elif char == "/":
                            client.send_keypress(KeyCodes.SLASH)
                        elif char == ".":
                            client.send_keypress(KeyCodes.DOT)
                        elif char == ",":
                            client.send_keypress(KeyCodes.COMMA)
                        elif char == "|":
                            client.send_keypress(KeyCodes.PIPE)
                        elif char == "-":
                            client.send_keypress(KeyCodes.MINUS)
                        elif char == "=":
                            client.send_keypress(KeyCodes.EQUAL)
                        elif char in shift_required_characters:
                            key_code_str = char_to_key_code(char)
                            if key_code_str:
                                key_code = getattr(KeyCodes, key_code_str)
                                client.send_keyboard_combination(ModifierCodes.SHIFT, key_code)
                            else:
                                logger.warning(f"Unsupported character '{char}' in Duckyscript")
                        elif char.isalpha():
                            key_code = getattr(KeyCodes, char.lower())
                            if char.isupper():
                                client.send_keyboard_combination(ModifierCodes.SHIFT, key_code)
                            else:
                                client.send_keypress(key_code)
                        else:
                            key_code = char_to_key_code(char)
                            if key_code:
                                client.send_keypress(key_code)
                            else:
                                logger.warning(f"Unsupported character '{char}' in Duckyscript")

                        current_position = char_position

                    except AttributeError as e:
                        logger.warning(f"Attribute error: {e} - Unsupported character '{char}' in Duckyscript")

            elif any(mod in line for mod in ["SHIFT", "ALT", "CTRL", "GUI", "COMMAND", "WINDOWS"]):
                components = line.split()
                if len(components) == 2:
                    modifier, key = components
                    try:
                        modifier_enum = getattr(ModifierCodes, modifier.upper())
                        key_enum = getattr(KeyCodes, key)
                        client.send_keyboard_combination(modifier_enum, key_enum)
                        logger.info(f"Sent combination: {line}")
                    except AttributeError:
                        logger.warning(f"Unsupported combination: {line}")
                else:
                    logger.warning(f"Invalid combination format: {line}")
            elif line.startswith("ENTER"):
                client.send_keypress(KeyCodes.ENTER)
            elif line.startswith("PRINTSCREEN"):
                client.send_keypress(KeyCodes.PRINTSCREEN)
            elif line.startswith("DOWN"):
                client.send_keypress(KeyCodes.DOWN)
            elif line.startswith("LEFT"):
                client.send_keypress(KeyCodes.LEFT)
            current_position = 0
            current_line += 1

    except ReconnectionRequiredException:
        raise ReconnectionRequiredException("Reconnection required", current_line, current_position)
    except Exception as e:
        logger.error(f"Error during script execution: {e}")