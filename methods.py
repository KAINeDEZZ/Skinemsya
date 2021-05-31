from aiohttp.web import json_response
import aiofile

import datetime
import json

import utils
from database import User, Purchase, Product, Invites


async def auth(request, sign, vk_user_id):
    params = dict(request.query)

    async with aiofile.async_open('keys.json', 'r') as file:
        secret_key = json.loads(await file.read())['secret_key']

    status = utils.is_valid(params, sign, secret_key)

    if status:
        token = utils.create_token(50)
        now = datetime.datetime.now()
        user_data = await User.request(user_id=vk_user_id)

        if not user_data:
            await User.async_create(
                user_id=vk_user_id,
                token=token,
                last_active=now
            )

        else:
            user_data = user_data[0]
            user_data.token = token
            user_data.last_active = now

            await User.async_update(user_data)

        return json_response({'token': token})

    else:
        return json_response({}, status=400)


async def get_all_purchases(user_id):
    """
    Получение всех закупок

    :param user_id: ID пользователя
    :type user_id: int

    :return: Response
    """
    user_data = await User.objects.get(User, user_id=user_id)

    purchases = []
    for purchase in await Purchase.execute(user_data.purchase.order_by(Purchase.status)):
        purchases.append(purchase.to_json())

    return json_response(purchases)


async def get_purchase(user_id, purchase_id):
    """
    Получение данных о закупки

    :param purchase_id:
    :type purchase_id; int

    :return: Response
    """
    purchase_data = await Purchase.request(id=purchase_id)
    if not purchase_data:
        return json_response({'error': 'Purchase not found'}, status=404)

    purchase_data = purchase_data[0]
    if purchase_data.owner.user_id != int(user_id):
        return json_response({'error': 'No permissions'}, status=400)

    return json_response(purchase_data.to_json())


async def create_purchase(user_id, title, billing_at, ending_at, description=None):
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
        billing_at = datetime.datetime.strptime(billing_at, '%Y-%m-%dT%H:%M')
        ending_at = datetime.datetime.strptime(ending_at, '%Y-%m-%dT%H:%M')
    except ValueError:
        return json_response({'error': 'Invalid datetime'}, status=400)

    now = datetime.datetime.now().replace(microsecond=0)

    if not (now < billing_at < ending_at):
        return json_response({'error': 'Invalid datetime'}, status=400)

    user_data = await utils.get_user_data(user_id)
    purchase_data = await Purchase.async_create(
        owner=user_data,
        title=title,
        description=description,

        created_at=datetime.datetime.now(),
        billing_at=billing_at,
        ending_at=ending_at,
    )

    purchase_data.users.add(user_data)
    return json_response(purchase_data.to_json())


async def edit_purchase(user_id, purchase_id, title=None, description=None, billing_at=None, ending_at=None):
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


async def delete_purchase(user_id, purchase_id):
    user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
    if not purchase_data:
        return user_data

    await Purchase.objects.delete(purchase_data)

    return json_response({'deleted_id': purchase_id})


async def get_members(purchase_id):
    purchase_data = await Purchase.request(id=purchase_id)
    if not purchase_data:
        return json_response({'error': 'Cant find purchase with this id'}, status=404)

    purchase_data = purchase_data[0]
    members = [member.user_id for member in await User.execute(purchase_data.users)]
    return json_response(members)


async def delete_member(user_id, purchase_id, target_id):
    user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
    if not purchase_data:
        return user_data

    target_data = await User.request(user_id=target_id)
    if not target_data:
        return json_response({'error': 'Cant find user with this id'}, status=404)
    target_data = target_data[0]

    if not await User.execute(purchase_data.users.where(User.user_id==target_id)):
        return json_response({'error': 'Cant find target with this id in purchase'}, status=404)

    purchase_data.users.remove(target_data)
    return json_response({'deleted': target_id})


async def get_invites(user_id):
    invites = [invite.purchase.to_json() for invite in await Invites.request(user_id=user_id)]
    return json_response(invites)


async def create_invite(user_id, purchase_id, target_id):
    user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
    if not purchase_data:
        return user_data

    await Invites.async_create(user_id=target_id, purchase=purchase_data)
    return json_response({'invited': {'user_id': target_id, 'purchase_id': purchase_id}})


async def delete_invite(user_id, purchase_id, target_id):
    user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
    if not purchase_data:
        return user_data

    invite_data = await Invites.request(user_id=target_id, purchase=purchase_data)
    if not invite_data:
        return json_response({'error': 'Cant find invite with this id'}, status=404)
    invite_data = invite_data[0]

    await Invites.objects.delete(invite_data)
    return json_response({'deleted': invite_data.id})


async def confirm_invite(user_id, purchase_id):
    purchase_data = await Purchase.request(id=purchase_id)
    if not purchase_data:
        return json_response({'error': 'Cant find purchase with this id'}, status=404)
    purchase_data = purchase_data[0]

    invite_data = await Invites.request(user_id=user_id, purchase=purchase_data)
    if not invite_data:
        return json_response({'error': 'Cant find invite for u'}, status=404)
    invite_data = invite_data[0]

    user_data = await User.objects.get(User, user_id=user_id)
    purchase_data.users.add(user_data)
    await Invites.objects.delete(invite_data)

    return json_response({'added_to': purchase_id})


async def refuse_invite(user_id, purchase_id):
    purchase_data = await Purchase.request(id=purchase_id)
    if not purchase_data:
        return json_response({'error': 'Cant find purchase with this id'}, status=404)
    purchase_data = purchase_data[0]

    invite_data = await Invites.request(user_id=user_id, purchase=purchase_data)
    if not invite_data:
        return json_response({'error': 'Cant find invite with this id'}, status=404)
    invite_data = invite_data[0]

    await Invites.objects.delete(invite_data)
    return json_response({'refused': invite_data.id})


async def get_products(user_id, purchase_id):
    user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
    if not purchase_data:
        return user_data

    products_data = list(obj.to_json() for obj in await Product.request(purchase=purchase_data))
    return json_response(products_data)


async def create_product(user_id, purchase_id, title, cost, description=None):
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
    user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
    if not purchase_data:
        return user_data

    cost = int(cost)
    if cost < 0:
        return json_response({'error': 'Invalid cost'}, status=400)

    product_data = await Product.async_create(
        title=title,
        description=description,
        cost=cost,
        purchase_id=purchase_data.id
    )

    return json_response({
        # TODO
    })


async def edit_product(user_id, purchase_id, product_id, title=None, description=None, cost=None):
    """
    Редактирование продукта

    :param product_id: ID Продукта
    :type product_id: int

    :param title: Название продукта
    :type title: str

    :param description: Описание продукта
    :type description: str

    :param cost: Цена продукта
    :type cost: int

    :return: Response
    """
    user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
    if not purchase_data:
        return user_data

    product_data = await Product.request(id=product_id)
    if not product_data:
        return json_response({'error': 'Product not found'}, status=404)

    product_data = purchase_data[0]

    if cost and cost < 0:
        return json_response({'error': 'Invalid cost'}, status=400)

    was_set = []
    if title:
        product_data.title = title
        was_set.append('title')

    if description:
        product_data.description = description
        was_set.append('description')

    if cost:
        product_data.cost = cost
        was_set.append('cost')

    await Product.async_update(product_data)
    return json_response({'was_set': was_set})


async def delete_product(user_id, purchase_id, product_id):
    user_data, purchase_data = await utils.check_purchase_permission(user_id, purchase_id)
    if not purchase_data:
        return user_data

    product_data = await Product.request(id=product_id)
    if not product_data:
        return json_response({'error': 'Product not found'}, status=404)

    await Product.objects.delete(product_data)
    return json_response({'deleted': product_id})
