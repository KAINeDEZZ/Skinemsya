from aiohttp.web import post, get
from methods import *

routes = [
    get('/auth/', auth),

    get('/get_all_purchases/', get_all_purchases),

    get('/get_purchase/', get_purchase),
    get('/create_purchase/', create_purchase),
    get('/edit_purchase/', edit_purchase),
    post('/delete_purchase/', delete_purchase),

    get('/create_product/', create_product),
    get('/edit_product/', edit_product)
]