from cryptography.fernet import Fernet
message = "mypassword".encode()

with open("key2.key", "rb") as f:
    key = f.read()
f = Fernet(key)
encrypted = f.encrypt(message)
print(encrypted)
print()
decrypted = f.decrypt(encrypted)
print(decrypted.decode(), type(decrypted))