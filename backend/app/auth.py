import hashlib
import hmac
import json
import time
from typing import Optional
from urllib.parse import parse_qsl, unquote

from fastapi import Header, HTTPException

from . import appdb
from .config import settings


def verify_max_init_data(init_data: str, bot_token: str, ttl: int) -> Optional[dict]:
    if not init_data or not bot_token:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError:
        return None
    received = pairs.pop("hash", None)
    if not received:
        return None

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received.lower()):
        return None

    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError:
        return None
    # auth_date в секундах; на случай миллисекунд - нормализуем
    if auth_date > 10**11:
        auth_date //= 1000
    if ttl > 0 and time.time() - auth_date > ttl:
        return None

    try:
        user = json.loads(pairs.get("user", ""))
    except ValueError:
        return None
    if not isinstance(user, dict) or "id" not in user:
        return None
    return user


def _account_key(x_device_id: Optional[str], x_max_init_data: Optional[str]) -> Optional[str]:
    if x_max_init_data:
        # Фронтенд кодирует initData через encodeURIComponent: заголовок latin-1, а имя кириллицей
        user = verify_max_init_data(unquote(x_max_init_data), settings.max_bot_token, settings.max_init_data_ttl)
        if user:
            return f"max:{user['id']}"
    return x_device_id or None


def optional_user_id(
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
    x_max_init_data: Optional[str] = Header(None, alias="X-Max-Init-Data"),
) -> Optional[int]:
    key = _account_key(x_device_id, x_max_init_data)
    return appdb.get_or_create_user(key) if key else None


def require_user_id(
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
    x_max_init_data: Optional[str] = Header(None, alias="X-Max-Init-Data"),
) -> int:
    key = _account_key(x_device_id, x_max_init_data)
    if not key:
        raise HTTPException(status_code=400, detail="Нужен заголовок X-Device-Id")
    return appdb.get_or_create_user(key)
