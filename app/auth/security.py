import bcrypt

def hash_password(plain_password: str) -> str:
    """Return bcrypt hash of the given password."""
    # bcrypt requires bytes
    password_bytes = plain_password.encode('utf-8')
    # Hash the password with a generated salt
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    # Return as a string to store in the DB
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the hash."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        return False
