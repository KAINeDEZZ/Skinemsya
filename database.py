import peewee

from database_driver import AsyncModel


class User(AsyncModel):
    user_id = peewee.IntegerField()
    token = peewee.CharField(max_length=100)
    last_active = peewee.DateTimeField(null=True)

    def __str__(self):
        return f'{self.user_id} {self.last_active}'


class Purchase(AsyncModel):
    class Status:
        PICK = 'pick'
        BILL = 'bill'
        FINIS = 'finish'
        CHOOSES = (
            (0, PICK),
            (1, BILL),
            (2, FINIS)
        )

    owner = peewee.ForeignKeyField(User)
    users = peewee.ManyToManyField(User, backref='purchase')
    status = peewee.CharField(max_length=20, choices=Status.CHOOSES, default=Status.PICK)

    title = peewee.CharField(max_length=20)
    description = peewee.CharField(max_length=100, null=True)

    created_at = peewee.DateTimeField()
    billing_at = peewee.DateTimeField()
    ending_at = peewee.DateTimeField()

    def __str__(self):
        return f'{self.owner} {self.title} {self.status}'


class Product(AsyncModel):
    title = peewee.CharField(max_length=30)
    description = peewee.CharField(max_length=100, null=True)
    cost = peewee.IntegerField()

    purchase = peewee.ForeignKeyField(Purchase, backref='products')

    def __str__(self):
        return f'{self.title} {self.cost}'


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

    def __str__(self):
        return f'{self.user} {self.status}'


User.create_table()
Purchase.create_table()
Product.create_table()
UserBill.create_table()
