import base64
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


if __name__ == "__main__":
    password_provided = "sometextishereforpasswordencrypt"  # This is input in the form of a string
    password = password_provided.encode()  # Convert to type bytes
    salt = os.urandom(16)  # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password)) # Can only use kdf once
    print(key)
    # with open("key2.key", "wb") as f:
    #     f.write(key)
