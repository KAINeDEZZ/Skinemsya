import peewee
import peewee_async
import database

import sys
import asyncio


if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


database = peewee_async.PostgresqlDatabase(
    database='servermanager',
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
    async def async_create(cls, **query):
        await objects.create(cls, **query)

    @classmethod
    async def execute(cls, selector):
        return await cls.objects.execute(selector)

    @classmethod
    async def async_update(cls, obj, only=None):
        await cls.objects.update(obj, only=only)
