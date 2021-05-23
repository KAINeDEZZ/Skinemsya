from aiohttp import web

import datetime
import inspect

from routes import routes


class Core:
    def __init__(self):
        self.app = web.Application()
        self.app.add_routes(routes)
        self.app.middlewares.append(self.print_request)
        self.app.middlewares.append(self.allow_all_hosts_setter)
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

    @staticmethod
    @web.middleware
    async def allow_all_hosts_setter(request, handler):
        response = await handler(request)
        response.headers.add('Access-Control-Allow-Origin', '*')
        print(response.headers)
        return response

    def run(self):
        web.run_app(self.app, port=8082)


if __name__ == '__main__':
    core = Core()
    core.run()
