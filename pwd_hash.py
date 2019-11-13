from cryptography.fernet import Fernet
import typing
import base64
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def gen_save_key() -> bytes:
    """
    generate and store a Fernet key
    :return key: binary key
    """
    filename = "key.key"
    key = Fernet.generate_key()
    with open(filename, "wb") as f:
        f.write(key)
    return key


def load_key() -> bytes:
    """
    load a generated key from key.key file
    :return: binary key
    """
    filename = "key.key"
    with open(filename, "rb") as f:
        key = f.read()
    return key


if __name__ == "__main__":
    key = load_key()
    print(key)