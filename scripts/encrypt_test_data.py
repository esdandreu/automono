"""
Utilities for encrypting and decrypting test data using REPSOL_PASSWORD.

This allows us to store sensitive test PDFs in the repository without exposing
actual invoice data.
"""

from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


def get_encryption_key(password: str) -> bytes:
    """Generate encryption key from password using PBKDF2."""
    # Convert password to bytes
    password_bytes = password.encode("utf-8")

    # Use a fixed salt for reproducible encryption (in production, use random salt)
    salt = b"repsol_test_salt_2024"  # Fixed salt for test data

    # Derive key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
    return key


def encrypt_file(input_path: Path, output_path: Path, password: str) -> None:
    """
    Encrypt a file using the given password.

    Args:
        input_path: Path to the file to encrypt
        output_path: Path where the encrypted file will be saved
        password: Password to use for encryption
    """
    key = get_encryption_key(password)
    fernet = Fernet(key)

    with open(input_path, "rb") as file:
        original_data = file.read()

    encrypted_data = fernet.encrypt(original_data)

    with open(output_path, "wb") as file:
        file.write(encrypted_data)


def decrypt_file(input_path: Path, output_path: Path, password: str) -> None:
    """
    Decrypt a file using the given password.

    Args:
        input_path: Path to the encrypted file
        output_path: Path where the decrypted file will be saved
        password: Password to use for decryption
    """
    key = get_encryption_key(password)
    fernet = Fernet(key)

    with open(input_path, "rb") as file:
        encrypted_data = file.read()

    decrypted_data = fernet.decrypt(encrypted_data)

    with open(output_path, "wb") as file:
        file.write(decrypted_data)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Encrypt test PDF files for safe storage in the repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python encrypt_test_data.py invoice.pdf repsol_invoice $REPSOL_PASSWORD
        """,
    )
    parser.add_argument(
        "input_path", type=Path, help="Path to the input file to encrypt"
    )
    parser.add_argument(
        "output_path", type=Path, help="Path to the output encrypted file"
    )
    parser.add_argument("password", help="Password to use for encryption")

    args = parser.parse_args()

    if not args.input_path.exists():
        print(f"Error: Input file {args.input_path} does not exist")
        sys.exit(1)

    try:
        encrypt_file(args.input_path, args.output_path, args.password)
        print(f"Successfully encrypted {args.input_path} to {args.output_path}")
    except Exception as e:
        print(f"Error encrypting file: {e}")
        sys.exit(1)
