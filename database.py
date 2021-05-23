import peewee

from database_driver import AsyncModel


class User(AsyncModel):
    user_id = peewee.IntegerField()
    token = peewee.CharField(max_length=100)
    last_active = peewee.DateTimeField(null=True)


class Purchase(AsyncModel):
    class Status:
        CHOOSES = ()

    owner = peewee.ForeignKeyField(User)
    users = peewee.ManyToManyField(User, backref='purchase')
    status = peewee.CharField(max_length=20, choices=Status.CHOOSES)

    title = peewee.CharField(max_length=20)
    description = peewee.CharField(max_length=100)

    created_at = peewee.DateTimeField()
    billing_at = peewee.DateTimeField()
    ending_at = peewee.DateTimeField()


class Product(AsyncModel):
    title = peewee.CharField(max_length=30)
    description = peewee.CharField(max_length=100, null=True)
    cost = peewee.IntegerField()

    purchase = peewee.ForeignKeyField(Purchase, backref='products')


class UserBill(AsyncModel):
    class Status:
        WAIT = 'wait'
        SENT = 'sent'
        CONFIRM = 'confirm'

        CHOOSES = (WAIT, SENT, CONFIRM)

    products = peewee.ManyToManyField(Product, backref='user_bill')
    purchase = peewee.ForeignKeyField(Purchase, backref='user_bill')
    user = peewee.ForeignKeyField(User, backref='user_bill')
    status = peewee.CharField(max_length=20, choices=Status.CHOOSES, default=Status.WAIT)


User.create_table()
Purchase.create_table()
Product.create_table()
UserBill.create_table()
