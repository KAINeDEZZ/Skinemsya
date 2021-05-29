from aiohttp.web import json_response
import aiofile

import datetime
import json

import utils
from database import User, Purchase, Product


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

    return json_response({})


async def get_purchase(user_id, purchase_id):
    """
    Получение данных о закупки

    :param purchase_id:
    :type purchase_id; int

    :return: Response
    """
    return json_response({})


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

    if cost < 0:
        return json_response({'error': 'Invalid cost'}, status=400)

    product_data = await Product.async_create(
        title=title,
        description=description,
        cost=cost,
        purchase=purchase_data
    )

    return json_response(product_data.to_json())


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
