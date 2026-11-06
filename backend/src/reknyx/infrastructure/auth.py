"""Opaque server sessions and salted scrypt password hashes; no client actors."""
import base64
import hashlib
import hmac
import secrets


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()


def verify_password(password, encoded):
    try:
        kind, n, r, p, salt, digest = encoded.split("$")
        if (kind, n, r, p) != ("scrypt", "16384", "8", "1"):
            return False
        salt, digest = base64.urlsafe_b64decode(salt), base64.urlsafe_b64decode(digest)
        if len(salt) != 16 or len(digest) != 32:
            return False
        computed = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
        return hmac.compare_digest(computed, digest)
    except (ValueError, TypeError):
        return False


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()
