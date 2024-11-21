# config.py
import os

from dotenv import dotenv_values

config = {
    **os.environ,
    **dotenv_values(".env", verbose=True),
}

MODEL_SOURCE = config.get("MODEL_SOURCE", "Bedrock")
