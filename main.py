from aiohttp import web

import datetime
import inspect

from routes import routes
from database import User


class Core:
    def __init__(self):
        self.app = web.Application()
        self.app.add_routes(routes)
        self.app.middlewares.append(self.print_request)
        self.app.middlewares.append(self.allow_all_hosts_setter)
        self.app.middlewares.append(self.token_checker)
        self.app.middlewares.append(self.args_loader)

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

    def run(self):
        web.run_app(self.app, port=8082)

    @staticmethod
    @web.middleware
    async def token_checker(request, handler):
        if handler.__name__ != 'auth':
            params = dict(request.query)

            user_id = params.get('user_id')
            token = params.get('token')

            if not user_id or not token:
                return web.json_response({'error': 'Invalid params'}, status=400)

            if not user_id.isdigit():
                return web.json_response({'error': 'Invalid params'}, status=400)

            user_id = int(user_id)
            user_data = await User.request(user_id=user_id)

            if not user_data:
                return web.json_response({'error': 'Invalid params'}, status=400)

            user_data = user_data[0]
            if user_data.token != token:
                return web.json_response({'error': 'Invalid token'}, status=400)

        return await handler(request)

    @staticmethod
    @web.middleware
    async def args_loader(request, handler):
        params = dict(request.query)
        signature = inspect.signature(handler)

        kwargs = {}
        for param in signature.parameters.values():
            if param.name != 'request':
                if param.default is inspect.Parameter.empty and not params.get(param.name):
                    return web.json_response({'error': 'Invalid params'}, status=400)

                elif params.get(param.name):
                    if params[param.name] == 'True':
                        kwargs[param.name] = True

                    elif params[param.name] == 'False':
                        kwargs[param.name] = False

                    else:
                        kwargs[param.name] = params[param.name]

            else:
                kwargs[param.name] = request

        response = await handler(**kwargs)
        return response


if __name__ == '__main__':
    core = Core()
    core.run()
