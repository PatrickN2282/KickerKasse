import bcrypt
from functools import lru_cache


class PasswordHasher:
    """Password hashing with bcrypt"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


@lru_cache(maxsize=None)
def get_password_hasher() -> PasswordHasher:
    return PasswordHasher()
