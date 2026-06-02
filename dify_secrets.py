import base64
import hashlib


def mask_api_key(api_key):
    """Return a masked API key for safe display/storage in logs or UI."""
    value = (api_key or '').strip()
    if not value:
        return ''
    if len(value) <= 6:
        return '*' * len(value)
    if len(value) <= 12:
        return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def _keystream(secret_key, length):
    seed = (secret_key or 'ctf-platform-default-key').encode('utf-8')
    digest = hashlib.sha256(seed).digest()
    repeats = (length // len(digest)) + 1
    return (digest * repeats)[:length]


def obfuscate_api_key(api_key, secret_key):
    """Obfuscate API key so plaintext is not stored directly in database."""
    value = (api_key or '').strip()
    if not value:
        return ''
    raw = value.encode('utf-8')
    stream = _keystream(secret_key, len(raw))
    mixed = bytes(b ^ stream[i] for i, b in enumerate(raw))
    return base64.urlsafe_b64encode(mixed).decode('ascii')


def reveal_api_key(token, secret_key):
    """Recover API key from obfuscated token."""
    value = (token or '').strip()
    if not value:
        return ''
    try:
        mixed = base64.urlsafe_b64decode(value.encode('ascii'))
        stream = _keystream(secret_key, len(mixed))
        raw = bytes(b ^ stream[i] for i, b in enumerate(mixed))
        return raw.decode('utf-8')
    except Exception:
        return ''