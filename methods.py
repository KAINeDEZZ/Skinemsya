from aiohttp.web import json_response
import aiofile

import datetime
import json

from tortoise.functions import Count
from tortoise.query_utils import Prefetch, Q

import utils
from models import User, Purchase, Invites, Product, Bill, PurchaseStatus, BillStatus


async def auth(request, sign, vk_user_id):
    params = dict(request.query)

    async with aiofile.async_open('keys.json', 'r') as file:
        secret_key = json.loads(await file.read())['secret_key']

    status = utils.is_valid(params, sign, secret_key)

    if status:
        token = utils.create_token(50)
        now = datetime.datetime.now()
        user_data = await User.filter(user_id=vk_user_id).first()

        if not user_data:
            await User.create(
                user_id=vk_user_id,
                token=token,
                last_active=now
            )

        else:
            user_data.token = token
            user_data.last_active = now

            await user_data.save()

        return json_response({'token': token})

    else:
        return json_response({}, status=400)


async def get_all_purchases(user_data):
    """
    Получение всех закупок

    :param user_id: ID пользователя
    :type user_id: int

    :return: Response
    """

    purchases = []
    end_purchases = []
    for purchase_data in await Purchase.filter(members=user_data).select_related('owner').order_by('ending_at'):
        purchase = {
            'id': purchase_data.pk,
            'status': purchase_data.status,

            'title': purchase_data.title,
            'description': purchase_data.description,

            'created_at': purchase_data.created_at.isoformat(),
            'billing_at': purchase_data.billing_at.isoformat(),
            'ending_at': purchase_data.ending_at.isoformat(),

            'invite_key': purchase_data.invite_key,
            'is_owner': True if purchase_data.owner == user_data else False
        }

        if purchase_data.status is PurchaseStatus.PICK:
            purchase['next_status'] = purchase_data.billing_at
            purchases.append(purchase)

        elif purchase_data.status is PurchaseStatus.BILL:
            purchase['next_status'] = purchase_data.ending_at
            purchases.append(purchase)

        else:
            end_purchases.append(purchase)

    purchases = sorted(purchases, key=lambda element: element['next_status'])
    for purchase in purchases:
        purchase.pop('next_status')

    return json_response(purchases + end_purchases)


async def get_purchase(purchase_data, user_data):
    """
    Получение данных о закупки

    :param purchase_id:
    :type purchase_id; int

    :return: Response
    """
    return json_response({
        'is_owner': True if purchase_data.owner == user_data else False,
        'title': purchase_data.title,
        'description': purchase_data.description,
        'status': purchase_data.status,

        'created_at': purchase_data.created_at.isoformat(),
        'billing_at': purchase_data.billing_at.isoformat(),
        'ending_at': purchase_data.ending_at.isoformat(),
    })


async def create_purchase(user_data, title, billing_at, ending_at, description=None):
    """
    Создание закупки

    :param user_id: ID пользователя
    :type user_id: int

    :param title:
    :type title: str

    :param description:
    :type description: str

    :return: Response
    """
    try:
        billing_at = datetime.date.fromisoformat(billing_at)
        ending_at = datetime.date.fromisoformat(ending_at)
    except ValueError:
        return json_response({'error': 'Invalid datetime'}, status=400)

    now = datetime.date.today()

    if not (now < billing_at < ending_at):
        return json_response({'error': 'Invalid datetime'}, status=400)

    purchase_data = await Purchase.create(
        owner=user_data,
        title=title,
        description=description,

        created_at=now,
        billing_at=billing_at,
        ending_at=ending_at,

        invite_key=utils.create_token(20)
    )

    await purchase_data.members.add(user_data)
    await Bill.create(
        user=user_data,
        purchase=purchase_data,
    )

    return json_response({'created': purchase_data.pk})


# async def edit_purchase(user_id, purchase_id, title=None, description=None, billing_at=None, ending_at=None):
#     # TODO
#     """
#     Редактирование закупки
#
#     :param purchase_id:
#     :type purchase_id: int
#
#     :param title:
#     :type title: str
#
#     :param description:
#     :type description: str
#
#     :return: Response
#     """
#     user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
#     if not purchase_data:
#         return user_data
#
#     was_set = []
#     if title:
#         purchase_data.title = title
#         was_set.append('title')
#
#     if description:
#         purchase_data.description = description
#         was_set.append('description')
#
#     if billing_at or ending_at:
#         billing_at = utils.load_datetime(billing_at)
#         ending_at = utils.load_datetime(ending_at)
#
#         if (billing_at and ending_at and not purchase_data.start_at < billing_at < ending_at) or \
#                 (billing_at and not purchase_data.start_at < billing_at) or \
#                 (ending_at and not purchase_data.start_at < ending_at):
#             return json_response({'error': 'Invalid datetime'}, status=400)
#
#         if billing_at:
#             purchase_data.billing_at = billing_at
#             was_set.append('billing_at')
#
#         if ending_at:
#             purchase_data.ending_at = ending_at
#             was_set.append('ending_at')
#
#     await Purchase.async_update(purchase_data)
#     return json_response({'was_set': was_set})


async def delete_purchase(purchase_data, is_owner):
    if not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    await Purchase.delete(purchase_data)
    return json_response({'deleted_id': purchase_data.pk})


async def get_members(purchase_data):
    members = [member.user_id for member in await purchase_data.members.all()]
    return json_response(members)


async def delete_member(user_id, purchase_data, is_owner, target_id):
    if not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    if is_owner and user_id == target_id:
        return json_response({'error': 'Cant self delete'}, status=400)

    target_data = await purchase_data.members.filter(user_id=target_id).first()
    if not target_data:
        return json_response({'error': 'Cant find user with this id'}, status=404)

    await purchase_data.members.remove(target_data)
    return json_response({'deleted': target_id})


async def member_leave(user_data, purchase_data, is_owner):
    if is_owner:
        return json_response({'error': 'Cant leave from your purchase'}, status=400)

    await purchase_data.members.remove(user_data)
    return json_response({'purchase_id': purchase_data.pk})


async def get_invites(user_id):
    invites = []
    for invite in await Invites.filter(user_id=user_id).select_related('purchase'):
        invites.append({
            'id':  invite.pk,
            'title': invite.purchase.title,
            'description': invite.purchase.description,
        })

    return json_response(invites)


async def get_purchase_invites(purchase_data, is_owner):
    if not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    invites = [invite.user_id for invite in await purchase_data.invite.all()]
    return json_response(invites)


async def create_invite(purchase_data, is_owner, target_id):
    if not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    if await purchase_data.members.filter(pk=target_id):
        return json_response({'error': 'Target already in purchase'}, status=400)

    if await Invites.filter(user_id=target_id, purchase=purchase_data):
        return json_response({'error': 'Target already invited'}, status=400)

    await Invites.create(user_id=target_id, purchase=purchase_data)
    return json_response({'invited': {'user_id': target_id, 'purchase_id': purchase_data.pk}})


async def create_invite_row(purchase_data, is_owner, targets_ids):
    if not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    purchase_users = set(member.user_id for member in await purchase_data.members.all())
    purchase_users.update(set(invite.user_id for invite in await Invites.filter(purchase=purchase_data)))

    if type(targets_ids) is int:
        targets_ids = str(targets_ids)

    created_invites = []
    for target_id in targets_ids.split(', '):
        target_id = int(target_id)

        if not purchase_users.isdisjoint({target_id}):
            continue

        await Invites.create(user_id=target_id, purchase=purchase_data)
        created_invites.append(target_id)

    return json_response(created_invites)


async def delete_invite(purchase_data, is_owner, target_id):
    if not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    invite_data = await Invites.filter(user_id=target_id, purchase=purchase_data).first()
    if not invite_data:
        return json_response({'error': 'Target doesnt invited'}, status=400)

    await invite_data.delete()

    await invite_data.delete()
    return json_response({'invite_id': invite_data.pk})


async def confirm_invite(user_id, user_data, invite_id):
    invite_data = await Invites.filter(pk=invite_id, user_id=user_id).select_related('purchase').first()
    if not invite_data:
        return json_response({'error': 'Invite doesnt exist'}, status=400)

    await invite_data.purchase.members.add(user_data)
    await Bill.create(
        user=user_data,
        purchase=invite_data.purchase,
    )

    await invite_data.delete()
    return json_response({'purchase_id': invite_data.purchase.pk})


async def refuse_invite(user_id, invite_id):
    invite_data = await Invites.filter(pk=invite_id, user_id=user_id).first()
    if not invite_data:
        return json_response({'error': 'Invite doesnt exist'}, status=400)

    await invite_data.delete()
    return json_response({'invite_id': invite_id})


async def get_all_products(user_data, purchase_data):
    picked_products = set()
    for bill_products in await Product.filter(bills__user=user_data, bills__purchase=purchase_data):
        picked_products.add(bill_products.pk)

    products = []
    for product in await purchase_data.products.all():
        products.append({
            'id': product.pk,
            'title': product.title,
            'description': product.description,
            'cost':  product.cost,
            'picked': not picked_products.isdisjoint({product.pk})
        })

    return json_response(products)


async def create_product(purchase_data, title, cost, description=None):
    """
    Создание продукта

    :param title:
    :type title: str

    :param description:
    :type description: str

    :param cost: Цена продукта
    :type cost: int

    :return: Response
    """

    cost = int(cost)
    if cost < 0:
        return json_response({'error': 'Invalid cost'}, status=400)

    product_data = await Product.create(
        title=title,
        description=description,
        cost=cost,
        purchase_id=purchase_data.id
    )

    return json_response({'product_id': product_data.pk})


# async def edit_product(user_id, purchase_id, product_id, title=None, description=None, cost=None):
#     #TODO
#     """
#     Редактирование продукта
#
#     :param product_id: ID Продукта
#     :type product_id: int
#
#     :param title: Название продукта
#     :type title: str
#
#     :param description: Описание продукта
#     :type description: str
#
#     :param cost: Цена продукта
#     :type cost: int
#
#     :return: Response
#     """
#
#     user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
#     if not purchase_data:
#         return user_data
#
#     product_data = await Product.request(id=product_id)
#     if not product_data:
#         return json_response({'error': 'Product not found'}, status=404)
#
#     product_data = purchase_data[0]
#
#     if cost and cost < 0:
#         return json_response({'error': 'Invalid cost'}, status=400)
#
#     was_set = []
#     if title:
#         product_data.title = title
#         was_set.append('title')
#
#     if description:
#         product_data.description = description
#         was_set.append('description')
#
#     if cost:
#         product_data.cost = cost
#         was_set.append('cost')
#
#     await Product.async_update(product_data)
#     return json_response({'was_set': was_set})


async def delete_product(purchase_data, product_id):
    product_data = await purchase_data.products.filter(pk=product_id).first()

    if not product_data:
        return json_response({'error': 'Product not found'}, status=404)

    await product_data.delete()
    return json_response({'product_id': product_id})


async def bill_pick(user_data, purchase_data, product_id, product_status):
    if type(product_status) is not bool:
        return json_response({'error': 'Invalid status'}, status=400)

    product_data = await purchase_data.products.filter(pk=product_id).first()
    if not product_data:
        return json_response({'error': 'Product not found'}, status=404)

    bill_data = await purchase_data.bills.filter(user=user_data).first()
    if await product_data.bills.filter(pk=bill_data.pk).exists() == product_status:
        return json_response({'error': f'Status already {product_status}'}, status=400)

    if product_status:
        await bill_data.products.add(product_data)

    else:
        await bill_data.products.remove(product_data)

    return json_response({'product_id': product_id, 'product_status': product_status})


async def get_bill(purchase_data, user_data, is_owner, target_id=None):
    if target_id and not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    products_data = await Product.filter(purchase=purchase_data).annotate(bills_count=Count('bills__id'))

    if target_id:
        user_filter = Q(bills__user__user_id=target_id)
    else:
        user_filter = Q(bills__user=user_data)

    bill_products = set(
        await Product.filter(user_filter, purchase=purchase_data).values_list('id', flat=True)
    )

    products = []
    bill = 0
    for product in products_data:
        if not bill_products.isdisjoint({product.pk}):
            bills_count = getattr(product, 'bills_count')
            user_cost = product.cost / bills_count

            if not user_cost.is_integer():
                user_cost = user_cost + 1

            user_cost = int(user_cost)
            bill += user_cost

            products.append({
                'title': product.title,
                'description': product.description,
                'cost': product.cost,
                'bills_count': bills_count,
                'user_cost': user_cost
            })

    return json_response({'bill': bill, 'products': products})


async def get_all_bills(purchase_data, is_owner):
    if not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    bills = [bill_data.user.user_id for bill_data in await Bill.filter(purchase=purchase_data).select_related('user')]
    return json_response(bills)


async def bill_status(purchase_data, user_data, is_owner, target_id=None):
    if target_id and not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    if target_id:
        user_filter = Q(user__user_id=target_id)
    else:
        user_filter = Q(user=user_data)

    bill_data = await Bill.filter(user_filter, purchase=purchase_data).first()
    return json_response({'status': bill_data.status})


async def bill_sent(purchase_data, user_data):
    if purchase_data.status is not PurchaseStatus.BILL:
        return json_response({'error': 'Method not allowed fot this purchase status'}, status=400)

    bill_data = await Bill.filter(purchase=purchase_data, user=user_data).first()
    bill_data.status = BillStatus.SENT
    await bill_data.save()

    return json_response({'bill_id': bill_data.pk})


async def bill_confirm(purchase_data, target_id, is_owner):
    if purchase_data.status is not PurchaseStatus.BILL:
        return json_response({'error': 'Method not allowed fot this purchase status'}, status=400)

    if not is_owner:
        return json_response({'error': 'No permissions'}, status=400)

    bill_data = await Bill.filter(purchase=purchase_data, user__user_id=target_id).first()
    bill_data.status = BillStatus.CONFIRM
    await bill_data.save()

    return json_response({'bill_id': bill_data.pk})
