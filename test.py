import datetime
import random
import requests

import database_driver
import models
import utils

models = [
    models.User,
    models.Purchase,
    models.Invites
]

def drop_tables():
    for table in models:
        table.truncate_table(cascade=True)

drop_tables()
# database_driver.database.drop_tables(models, save=False)

url = 'http://localhost:8082'


def call_method(method, user, **kwargs):
    del user['id']
    kwargs.update(user)

    return requests.get(f'{url}/{method}/', params=kwargs)


def get_date(offset):
    date = datetime.datetime.now() + datetime.timedelta(days=offset)
    return date.strftime('%Y-%m-%dT%H:%M')


def restore_decorator(func):
    def wrapper(*args, **kwargs):
        database_driver.database.create_tables(models)
        result = func(*args, **kwargs)
        drop_tables()
        return result

    return wrapper


def create_users(count):
    users = []
    users_ids = set()
    for _ in range(count):
        user_id = None
        while not user_id:
            user_id = random.randint(0, 100)
            if not users_ids.isdisjoint({user_id}):
                user_id = None

        token = random.randint(0,  100)
        user = models.User.create(user_id=user_id, token=token)

        users.append(user)
        users_ids.add(user_id)

    return users


def create_purchases(count, user_data):
    if type(user_data) is dict:
        user_data = models.User.get(models.User, user_id=user_data['user_id'])

    purchases = []
    for index in range(count):
        title = f'test_{index}'

        billing_at = datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 20))
        ending_at = billing_at + datetime.timedelta(days=random.randint(1, 20))

        purchase_data = models.Purchase.create(
            owner=user_data,
            title=title,
            created_at=datetime.datetime.now(),
            billing_at=billing_at,
            ending_at=ending_at,
            invite_key=utils.create_token(10)
        )
        purchase_data.users.add(user_data)

        purchases.append(purchase_data)
    return purchases


@restore_decorator
def test_purchase_create():
    users = create_users(1)
    params = {
        'title': 'test',
        'billing_at': get_date(1),
        'ending_at': get_date(2)
    }

    response = call_method('purchase/create', users[0].to_json(), **params)
    assert response.status_code == 200


@restore_decorator
def test_get_all_purchases():
    users = create_users(1)
    create_purchases(2, users[0])

    response = call_method('get_all_purchases', users[0].to_json())
    assert response.status_code == 200
    assert len(response.json()) == 2


@restore_decorator
def test_purchase_delete():
    users = create_users(1)
    purchases = create_purchases(1, users[0])

    assert call_method('purchase/delete', users[0].to_json(), purchase_id=purchases[0].id).status_code == 200


@restore_decorator
def test_get_purchase():
    users = create_users(2)
    purchases = create_purchases(1, users[0])
    purchases[0].users.add(users[1])

    assert call_method('purchase/get', users[0].to_json()).status_code == 400

    assert call_method('purchase/get', users[0].to_json(), purchase_id=purchases[0].id).status_code == 200
    assert call_method('purchase/get', users[1].to_json(), purchase_id=purchases[0].id).status_code == 200

