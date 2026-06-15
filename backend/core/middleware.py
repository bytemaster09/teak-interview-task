import logging
import time
import uuid

logger = logging.getLogger("blog")


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Accept a caller-supplied ID (useful for distributed tracing); otherwise mint one.
        rid = request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())[:8]
        request.request_id = rid

        t0 = time.monotonic()
        response = self.get_response(request)
        ms = int((time.monotonic() - t0) * 1000)

        response["X-Request-ID"] = rid
        logger.info("[%s] %s %s %d %dms", rid, request.method, request.path, response.status_code, ms)
        return response
