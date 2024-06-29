import os
import sys

from loguru import logger

TITLE = "BluePop"
VERSION = "v0.1"


ROOT_FOLDER = os.path.dirname(os.path.realpath(__file__))
PAYLOAD_FOLDER = os.path.join(f'{ROOT_FOLDER}/../', 'payloads/')

logger.remove()
logger.add(sys.stderr, level='DEBUG', colorize=True, backtrace=True, diagnose=True)
