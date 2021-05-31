from aiohttp.web import post, get
from methods import *
routes = [
    get('/auth/', auth),

    get('/get_all_purchases/', get_all_purchases),

    get('/purchase/get/', get_purchase),
    get('/purchase/create/', create_purchase),
    get('/purchase/edit/', edit_purchase),
    get('/purchase/delete/', delete_purchase),

    get('/members/get/', get_members),
    get('/members/delete/', delete_member),

    get('/invites/get/', get_invites),
    get('/invites/create/', create_invite),
    get('/invites/delete/', delete_invite),
    get('/invites/confirm/', confirm_invite),
    get('/invites/refuse/', refuse_invite),

    get('/get_products/', get_products),
    get('/create_product/', create_product),
    get('/edit_product/', edit_product)
]

