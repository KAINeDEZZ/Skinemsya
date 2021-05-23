from aiohttp.web import post, get
from methods import *

routes = [
    get('/auth/', auth),
    get('/', get_all_purchases)
]

