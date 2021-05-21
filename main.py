from aiohttp import web

import datetime

from routes import routes


class Core:
    def __init__(self):
        self.app = web.Application()
        self.app.add_routes(routes)
        self.app.middlewares.append(self.print_request)

    @staticmethod
    @web.middleware
    async def print_request(request, handler):
        response = await handler(request)
        time_label = f'{datetime.datetime.today().replace(microsecond=0)}'
        print(f'[{time_label}] [{response.status}] {request.url}')
        return response

    def run(self):
        web.run_app(self.app, port=8082)


if __name__ == '__main__':
    core = Core()
    core.run()
