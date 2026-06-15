from ninja import NinjaAPI
from ninja.errors import HttpError

from .accounts_api import router as auth_router
from .health import router as health_router
from .posts_api import router as posts_router
from .tags_api import router as tags_router

api = NinjaAPI(
    title="Blog API",
    version="1.0.0",
    description="Authors create posts; readers discover and comment on them.",
)

api.add_router("/auth", auth_router)
api.add_router("/posts", posts_router)
api.add_router("/tags", tags_router)
api.add_router("/health", health_router)


@api.exception_handler(HttpError)
def http_error_handler(request, exc: HttpError):
    return api.create_response(request, {"detail": exc.message}, status=exc.status_code)
