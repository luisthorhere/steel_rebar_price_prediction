import logging
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

log_file_path = os.path.join(BASE_DIR, "app.log")

logger = logging.getLogger("SteelRebarPricePrediction")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
