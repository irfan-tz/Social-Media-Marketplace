from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64

def generate_key_pair():
    """Generate a new RSA key pair"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    # Serialize keys to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return public_pem.decode(), private_pem.decode()

def encrypt_with_public_key(message, public_key_pem):
    """Encrypt data with public key"""
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode(),
        backend=default_backend()
    )

    # If message is a string, convert to bytes
    if isinstance(message, str):
        message = message.encode()

    encrypted = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted).decode()

def decrypt_with_private_key(encrypted_message, private_key_pem):
    """Decrypt data with private key"""
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
        backend=default_backend()
    )

    # Decode base64
    encrypted_data = base64.b64decode(encrypted_message)

    decrypted = private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # If the result is bytes, try to decode it to string
    if isinstance(decrypted, bytes):
        try:
            return decrypted.decode()
        except UnicodeDecodeError:
            return decrypted

    return decrypted
