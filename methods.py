from aiohttp.web import json_response
import aiofile

import datetime
import json

import utils
from models import User, Purchase, Invites


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
    for purchase in await Purchase.filter(members=user_data):
        purchases.append({
            'id': purchase.pk,
            'title': purchase.title,
            'description': purchase.description,
            'status': purchase.status,

            'created_at': purchase.created_at.isoformat(),
            'billing_at': purchase.billing_at.isoformat(),
            'ending_at': purchase.ending_at.isoformat(),

            'invite_key': purchase.invite_key,
        })

    return json_response(purchases)


async def get_purchase(purchase_data, user_data):
    """
    Получение данных о закупки

    :param purchase_id:
    :type purchase_id; int

    :return: Response
    """
    return json_response({
        'is_owner': 1 if purchase_data.owner == user_data else 0,
        'title': purchase_data.title,
        'description': purchase_data.description,
        'status': purchase_data.status,

        'created_at': purchase_data.created_at.isoformat(),
        'billing_at': purchase_data.billing_at.isoformat(),
        'ending_at': purchase_data.ending_at.isoformat(),
    })


async def is_purchase_owner(is_owner):
    return json_response({'is_owner': is_owner})


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
    return json_response({'created': purchase_data.pk})


async def edit_purchase(user_id, purchase_id, title=None, description=None, billing_at=None, ending_at=None):
    # TODO
    """
    Редактирование закупки

    :param purchase_id:
    :type purchase_id: int

    :param title:
    :type title: str

    :param description:
    :type description: str

    :return: Response
    """
    user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
    if not purchase_data:
        return user_data

    was_set = []
    if title:
        purchase_data.title = title
        was_set.append('title')

    if description:
        purchase_data.description = description
        was_set.append('description')

    if billing_at or ending_at:
        billing_at = utils.load_datetime(billing_at)
        ending_at = utils.load_datetime(ending_at)

        if (billing_at and ending_at and not purchase_data.start_at < billing_at < ending_at) or \
                (billing_at and not purchase_data.start_at < billing_at) or \
                (ending_at and not purchase_data.start_at < ending_at):
            return json_response({'error': 'Invalid datetime'}, status=400)

        if billing_at:
            purchase_data.billing_at = billing_at
            was_set.append('billing_at')

        if ending_at:
            purchase_data.ending_at = ending_at
            was_set.append('ending_at')

    await Purchase.async_update(purchase_data)
    return json_response({'was_set': was_set})


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
    await invite_data.delete()
    return json_response({'purchase_id': invite_data.purchase.pk})


async def refuse_invite(user_id, invite_id):
    invite_data = await Invites.filter(pk=invite_id, user_id=user_id).first()
    if not invite_data:
        return json_response({'error': 'Invite doesnt exist'}, status=400)

    await invite_data.delete()
    return json_response({'invite_id': invite_id})


#
#
# async def get_products(user_id, purchase_id):
#     user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
#     if not purchase_data:
#         return user_data
#
#     products_data = list(obj.to_json() for obj in await Product.request(purchase=purchase_data))
#     return json_response(products_data)
#
#
# async def create_product(user_id, purchase_id, title, cost, description=None):
#     """
#     Создание продукта
#
#     :param title:
#     :type title: str
#
#     :param description:
#     :type description: str
#
#     :param cost: Цена продукта
#     :type cost: int
#
#     :return: Response
#     """
#     user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
#     if not purchase_data:
#         return user_data
#
#     cost = int(cost)
#     if cost < 0:
#         return json_response({'error': 'Invalid cost'}, status=400)
#
#     product_data = await Product.async_create(
#         title=title,
#         description=description,
#         cost=cost,
#         purchase_id=purchase_data.id
#     )
#
#     return json_response({
#         # TODO
#     })
#
#
# async def edit_product(user_id, purchase_id, product_id, title=None, description=None, cost=None):
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
#
#
# async def delete_product(user_id, purchase_id, product_id):
#     user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
#     if not purchase_data:
#         return user_data
#
#     product_data = await Product.request(id=product_id)
#     if not product_data:
#         return json_response({'error': 'Product not found'}, status=404)
#
#     await Product.objects.delete(product_data)
#     return json_response({'deleted': product_id})
