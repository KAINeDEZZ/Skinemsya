import peewee
import peewee_async

import sys
import asyncio
import datetime


if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


database = peewee_async.PostgresqlDatabase(
    database='skinemsya',
    user='postgres',
    host='127.0.0.1',
    port='5432',
    password='4296'
)
objects = peewee_async.Manager(database)


class AdvanceSelector(peewee.ModelSelect):
    async def get_query(self):
        return await self.model.objects.exequte(self)


class AsyncModel(peewee.Model):
    class Meta:
        database = database

    objects = objects

    @classmethod
    async def request(cls, **kwargs):
        nodes = []
        for key, value in kwargs.items():
            field = getattr(cls, key, None)
            if not field:
                raise UnknownModelField(cls.__name__, key)

            nodes.append(field == value)

        selector = cls.select().where(*nodes) if nodes else cls.select()
        return await cls.execute(selector)

    @classmethod
    async def async_create(cls, **query):
        return await objects.create(cls, **query)

    @classmethod
    async def execute(cls, selector):
        return await cls.objects.execute(selector)

    @classmethod
    async def async_update(cls, obj, only=None):
        return await cls.objects.update(obj, only=only)

    def to_json(self):
        data = {}
        for key in self.__data__:
            value = self.__data__[key]

            if type(value) is datetime.datetime:
                value = f'{value.year}-{value.month}-{value.day}T{value.hour}:{value.min}'

            elif type(value) is datetime.date:
                value = f'{value.year}-{value.month}-{value.day}'

            data[key] = value

        return data


class UnknownModelField(Exception):
    def __init__(self, model, field):
        self.model = model
        self.field = field

    def __str__(self):
        return f'{self.model} has no {self.field} field'
