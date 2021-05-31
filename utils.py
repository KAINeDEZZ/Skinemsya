import random
from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlencode

from aiohttp.web import json_response

import datetime

from models import User, Purchase


def is_valid(query: dict, sign, secret: str) -> bool:
    """Check VK Apps signature"""
    vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
    hash_code = b64encode(HMAC(secret.encode(), urlencode(vk_subset, doseq=True).encode(), sha256).digest())
    decoded_hash_code = hash_code.decode('utf-8')[:-1].replace('+', '-').replace('/', '_')

    return sign == decoded_hash_code


def create_token(length):
    symbols = []
    for _ in range(length):
        symbol_type = random.randint(0, 2)
        if symbol_type == 0:
            symbol_code = random.randint(65, 90)

        elif symbol_type == 1:
            symbol_code = random.randint(97, 122)

        else:
            symbol_code = random.randint(48, 57)

        symbols.append(chr(symbol_code))

    return ''.join(symbols)
