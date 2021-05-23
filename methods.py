from aiohttp.web import json_response
import aiofile

import datetime
import json

import utils
from database import User


async def auth(request, sign, user_id):
    params = dict(request.query)

    async with aiofile.async_open('keys.json', 'r') as file:
        secret_key = json.loads(await file.read())['secret_key']

    status = utils.is_valid(params, sign, secret_key)

    if status:
        token = utils.create_token()
        now = datetime.datetime.now()
        user_data = await User.objects.execute(User.select().where(User.user_id == user_id))

        if not user_data:
            await User.async_create(
                user_id=user_id,
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


async def get_purchase(purchase_id):
    """
    Получение данных о закупки

    :param purchase_id:
    :type purchase_id; int

    :return: Response
    """
    return json_response({})


async def create_purchase(user_id, title, description=None):
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
    return json_response({})


async def edit_purchase(purchase_id, title=None, description=None):
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
    return json_response({})


async def create_product(title, cost, description=None):
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
    return json_response({})


async def edit_product(product_id, title=None, description=None, cost=None):
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

    return json_response({})
