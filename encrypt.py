from cryptography.fernet import Fernet
message = "beastfromeast".encode()

with open("key3.key", "rb") as f:
    key = f.read()
f = Fernet(key)
encrypted = f.encrypt(message)
print(encrypted)
print()
decrypted = f.decrypt(encrypted)
print(decrypted.decode(), type(decrypted))