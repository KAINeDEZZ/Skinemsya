from aiohttp.web import post, get
from methods import *
routes = [
    get('/auth/', auth),

    get('/purchase/get_all/', get_all_purchases),

    get('/purchase/get/', get_purchase),
    get('/purchase/is_owner/', is_purchase_owner),
    get('/purchase/create/', create_purchase),
    # get('/purchase/edit/', edit_purchase),
    get('/purchase/delete/', delete_purchase),

    get('/members/get/', get_members),
    get('/members/delete/', delete_member),
    get('/members/leave/', member_leave),

    get('/invites/get/', get_invites),
    get('/invites/get_purchase/', get_purchase_invites),
    get('/invites/create/', create_invite),
    get('/invites/create_row/', create_invite_row),
    get('/invites/delete/', delete_invite),
    get('/invites/confirm/', confirm_invite),
    get('/invites/refuse/', refuse_invite),

    get('/products/get_all/', get_all_products),
    get('/products/create/', create_product),
    # get('/products/edit/', edit_product),
    get('/products/delete/', delete_product),

    get('/bill/pick/', bill_pick),
    get('/bill/get/', get_bill),
    get('/bill/get_all/', get_all_bills),
    get('/bill/set_sent/', bill_sent),
    get('/bill/confirm/', bill_confirm),

]

