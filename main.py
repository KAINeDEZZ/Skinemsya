import asyncio

from aiohttp import web

import datetime
import inspect

from tortoise.query_utils import Q

from routes import routes
from models import User, Purchase, PurchaseStatus
from tortoise import Tortoise


class Core:
    def __init__(self):
        self.app = web.Application()
        self.app.add_routes(routes)

        self.app.on_startup.append(self.init_db)
        self.app.on_startup.append(self.background_task_factory)

        self.app.middlewares.append(self.add_middleware_data)
        self.app.middlewares.append(self.print_request)
        self.app.middlewares.append(self.allow_all_hosts_setter)
        self.app.middlewares.append(self.token_checker)
        self.app.middlewares.append(self.check_purchase_permissions)
        self.app.middlewares.append(self.args_loader)

    @staticmethod
    async def init_db(app):
        await Tortoise.init(
            db_url='postgres://postgres:4296@localhost:5432/skinemsya',
            modules={'models': ['models']}
        )

        await Tortoise.generate_schemas()

    @staticmethod
    @web.middleware
    async def add_middleware_data(request, handler):
        request.middleware_data = {}
        response = await handler(request)
        return response

    @staticmethod
    @web.middleware
    async def print_request(request, handler):
        response = await handler(request)
        time_label = f'{datetime.datetime.today().replace(microsecond=0)}'
        print(f'[{time_label}] [{response.status}] {request.url}')
        return response

    @staticmethod
    @web.middleware
    async def allow_all_hosts_setter(request, handler):
        response = await handler(request)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @staticmethod
    @web.middleware
    async def token_checker(request, handler):
        if request.url.path != '/auth/':
            params = dict(request.query)

            user_id = params.get('user_id')
            token = params.get('token')

            if not user_id or not token:
                return web.json_response({'error': 'Invalid params'}, status=400)

            if not user_id.isdigit():
                return web.json_response({'error': 'Invalid params'}, status=400)

            user_data = await User.filter(user_id=user_id).first()
            if not user_data:
                return web.json_response({'error': 'Invalid params'}, status=400)

            if user_data.token != token:
                return web.json_response({'error': 'Invalid token'}, status=400)

            user_data.last_active = datetime.datetime.now()
            await user_data.save()

            request.middleware_data = {
                'user_data': user_data
            }

        return await handler(request)

    @staticmethod
    @web.middleware
    async def check_purchase_permissions(request, handler):
        params = dict(request.query)

        purchase_id = params.get('purchase_id')

        if purchase_id:
            purchase_data = await Purchase.filter(pk=purchase_id).select_related('owner').first()
            if not purchase_data:
                return web.json_response({'error': 'Cant find purchase with this id'}, status=404)

            if purchase_data.owner == request.middleware_data['user_data']:
                request.middleware_data.update({
                    'purchase_data': purchase_data,
                    'is_owner': True,
                    'is_member': True
                })

            elif await purchase_data.members.filter(pk=request.middleware_data['user_data'].pk):
                request.middleware_data.update({
                    'purchase_data': purchase_data,
                    'is_owner': False,
                    'is_member': True
                })

            else:
                return web.json_response({'error': 'No permissions'}, status=400)

        result = await handler(request)
        return result

    @staticmethod
    @web.middleware
    async def args_loader(request, handler):
        params = dict(request.query)
        signature = inspect.signature(handler)

        kwargs = {}
        for param in signature.parameters.values():
            if param.name != 'request':
                param_value = params.get(param.name) or request.middleware_data.get(param.name)

                if param.default is inspect.Parameter.empty and param_value is None:
                    print(param.name) # TODO
                    return web.json_response({'error': 'Invalid params'}, status=400)

                elif param_value is not None:
                    if type(param_value) is str:

                        if param_value.isdigit():
                            kwargs[param.name] = int(param_value)

                        elif param_value.lower() == 'true':
                            kwargs[param.name] = True

                        elif param_value.lower() == 'false':
                            kwargs[param.name] = False

                        else:
                            kwargs[param.name] = param_value

                    else:
                        kwargs[param.name] = param_value

            else:
                kwargs[param.name] = request

        response = await handler(**kwargs)
        return response

    async def background_task_factory(self, app):
        asyncio.create_task(self.purchase_status_updater())

    @staticmethod
    async def purchase_status_updater():
        while True:
            print('Status handler')

            today = datetime.date.today()
            pick_to_bill = Q(billing_at__lte=today, status=PurchaseStatus.PICK)
            bill_to_end = Q(ending_at__lte=today, status=PurchaseStatus.BILL)
            pick_to_end = Q(ending_at__lte=today, status=PurchaseStatus.PICK)

            for purchase in await Purchase.filter(Q(pick_to_bill | bill_to_end | pick_to_end)):
                if purchase.ending_at <= today:
                    purchase.status = PurchaseStatus.END

                elif purchase.billing_at <= today:
                    purchase.status = PurchaseStatus.BILL

                else:
                    print(f'Background bug: {purchase.billing_at}, {purchase.ending_at}, {purchase.status}')

                await purchase.save()

            await asyncio.sleep(3600)

    def run(self):
        web.run_app(self.app, port=8082)


if __name__ == '__main__':
    core = Core()
    core.run()
