from aiohttp.web import Request, json_response
import utils

from database import User


async def auth(request):
    params = dict(request.query)
    status = utils.is_valid(query=params, secret="12")

    if status:
        return json_response({'token': '123456'}, headers={'Access-Control-Allow-Origin': '*'})
    else:
        return json_response({}, headers={'Access-Control-Allow-Origin': '*'}, status=400)


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
    return json_response()


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
    return json_response()


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
    return json_response()


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
    return json_response()


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

    return json_response()
