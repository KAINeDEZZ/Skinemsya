from tortoise.models import Model
from tortoise import fields

import enum


class PurchaseStatus(str, enum.Enum):
    PICK = 'pick'
    BILL = 'bill'
    FINIS = 'finish'


class User(Model):
    user_id = fields.IntField()
    token = fields.CharField(max_length=100)
    last_active = fields.DatetimeField(null=True)

    owned_purchase: fields.ReverseRelation['Purchase']
    purchase: fields.ManyToManyRelation['Purchase']

    def __str__(self):
        return f'{self.user_id} {self.last_active}'


class Purchase(Model):
    owner: fields.ForeignKeyRelation[User] = fields.ForeignKeyField('models.User', related_name='purchase_admin')
    members: fields.ManyToManyRelation[User] = fields.ManyToManyField('models.User', related_name='purchase')
    status = fields.CharEnumField(PurchaseStatus, max_length=20, default=PurchaseStatus.PICK)

    title = fields.CharField(max_length=20)
    description = fields.CharField(max_length=100, null=True)

    created_at = fields.DateField()
    billing_at = fields.DateField()
    ending_at = fields.DateField()

    invite_key = fields.CharField(max_length=100)
    invite: fields.ForeignKeyRelation['Invites']

    products: fields.ForeignKeyRelation['Product']

    def __str__(self):
        return f'{self.owner} {self.title} {self.status}'


class Invites(Model):
    user_id = fields.IntField()
    purchase: fields.ForeignKeyRelation[Purchase] = fields.ForeignKeyField('models.Purchase', related_name='invite')

    def __str__(self):
        return f'{self.user_id} {self.purchase}'


class Product(Model):
    title = fields.CharField(max_length=30)
    description = fields.CharField(max_length=100, null=True)
    cost = fields.IntField()

    purchase: fields.ForeignKeyRelation[Purchase] = fields.ForeignKeyField('models.Purchase', backref='products')

    def __str__(self):
        return f'{self.title} {self.cost}'


# class UserBill(database_driver.AsyncModel):
#     class Status:
#         WAIT = 'wait'
#         SENT = 'sent'
#         CONFIRM = 'confirm'
#
#         CHOOSES = (WAIT, SENT, CONFIRM)
#
#     products = peewee.ManyToManyField(Product, backref='user_bill')
#     purchase = peewee.ForeignKeyField(Purchase, backref='user_bill')
#     user = peewee.ForeignKeyField(User, backref='user_bill')
#     status = peewee.CharField(max_length=20, choices=Status.CHOOSES, default=Status.WAIT)
#
#     def __str__(self):
#         return f'{self.user} {self.status}'
# #
#
# database_driver.database.drop_tables([
#     # Invites
#     # User,
#     # Purchase,
#     # Purchase.users.get_through_model(),
#     # Product,
#     # UserBill,
# ])
#
#
# database_driver.database.create_tables([
#     User,
#     Purchase,
#     Purchase.users.get_through_model(),
#     Invites,
#     Product,
#     UserBill,
# ])
