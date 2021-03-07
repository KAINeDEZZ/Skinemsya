from aiohttp.web import UrlDispatcher, post, get
import views


def create_routes(router: UrlDispatcher):
    router.add_get('/test', views.get_all_purchases)

