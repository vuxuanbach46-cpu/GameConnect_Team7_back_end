from slowapi import Limiter
from slowapi.util import get_remote_address

# Settings reads .env as UTF-8; prevent SlowAPI from reopening it with the console encoding.
limiter = Limiter(key_func=get_remote_address, config_filename=__file__)
