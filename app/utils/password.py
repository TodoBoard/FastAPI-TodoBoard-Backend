from argon2.exceptions import VerifyMismatchError
from argon2 import PasswordHasher

hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    try:
        return hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
