import peewee
import peewee_async


# database = peewee_async.PostgresqlDatabase(
#     database='skinemsya',
#     user='postgres',
#     host='127.0.0.1',
#     port='5432',
#     password='4296'
# )


# class TestModel(peewee.Model):
#     text = peewee.TextField()
#
#     class Meta:
#         database = database
#
# print(TestModel.create_table())
# objects = peewee_async.Manager(database)
# objects.execute()
