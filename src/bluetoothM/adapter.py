from L2CAP.exceptions import ConnectionFailureException
from loguru import logger
from pydbus import SystemBus
from utils.menu_functions import run


class Adapter:
    def __init__(self, iface):
        self.iface = iface
        self.bus = SystemBus()
        self.adapter = self._get_adapter(iface)

    def _get_adapter(self, iface):
        try:
            return self.bus.get("org.bluez", f"/org/bluez/{iface}")
        except KeyError:
            logger.error(f"Unable to find bluetooth '{iface}', aborting.")
            raise ConnectionFailureException("Adapter not found")

    def _run_command(self, command):
        result = run(command)
        if result.returncode != 0:
            raise ConnectionFailureException(f"Failed to execute command: {' '.join(command)}. Error: {result.stderr}")

    def set_property(self, prop, value):
        value_str = str(value) if not isinstance(value, str) else value
        command = ["sudo", "hciconfig", self.iface, prop, value_str]
        self._run_command(command)

        verify_command = ["hciconfig", self.iface, prop]
        verification_result = run(verify_command)
        if value_str not in verification_result.stdout:
            logger.error(f"Unable to set bluetooth {prop}, aborting. Output: {verification_result.stdout}")
            raise ConnectionFailureException(f"Failed to set {prop}")

    def power(self, powered):
        self.adapter.Powered = powered

    def reset(self):
        self.power(False)
        self.power(True)

    def enable_ssp(self):
        try:
            ssp_command = ["sudo", "hciconfig", self.iface, "sspmode", "1"]
            ssp_result = run(ssp_command)
            if ssp_result.returncode != 0:
                logger.error(f"Failed to enable SSP: {ssp_result.stderr}")
                raise ConnectionFailureException("Failed to enable SSP")
        except Exception as e:
            logger.error(f"Error enabling SSP: {e}")
            raise