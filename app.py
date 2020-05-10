import logging
import src.url_handler
import src.img_handler
import src.start_handler

from src.client import client

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)
client.run_until_disconnected()
