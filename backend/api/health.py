from django.db import connection
from django.core.cache import cache
from ninja import Router

router = Router(tags=["ops"])


@router.get("", auth=None)
def health(request):
    result = {
        "status": "ok",
        "db": "ok",
        "cache": "ok",
        "cache_backend": type(cache).__name__,
    }

    try:
        connection.ensure_connection()
    except Exception as exc:
        result["db"] = str(exc)
        result["status"] = "degraded"

    try:
        cache.set("_hc", "1", 5)
        if cache.get("_hc") != "1":
            result["cache"] = "read-after-write mismatch"
            result["status"] = "degraded"
    except Exception as exc:
        result["cache"] = str(exc)
        result["status"] = "degraded"
    finally:
        cache.delete("_hc")

    return result
