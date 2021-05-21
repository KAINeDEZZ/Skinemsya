from aiohttp.web import post, get
from methods import *

routes = [
    get('/', test_view)
]

