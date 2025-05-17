from cryptography.fernet import Fernet
from django.conf import settings

def generate_group_key():
    return Fernet.generate_key()

def encrypt_file(file_data, key=None):
    cipher_suite = Fernet(key or settings.ENCRYPTION_KEY)
    return cipher_suite.encrypt(file_data)

def decrypt_file(encrypted_data, key=None):
    cipher_suite = Fernet(key or settings.ENCRYPTION_KEY)
    return cipher_suite.decrypt(encrypted_data)