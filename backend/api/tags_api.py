from typing import List

from django.core.cache import cache
from django.conf import settings
from ninja import Router
from ninja.errors import HttpError

from .auth import jwt_auth
from .schemas import ErrorOut, TagCreateIn, TagOut

router = Router(tags=["tags"])


@router.get("", response=List[TagOut])
def list_tags(request):
    cached = cache.get("tags:all")
    if cached:
        return cached

    from blog.models import Tag
    tags = list(Tag.objects.all().order_by("name"))
    result = [TagOut(id=t.pk, name=t.name, slug=t.slug) for t in tags]
    cache.set("tags:all", result, settings.CACHE_TTL_TAGS)
    return result


@router.post("", auth=jwt_auth, response={201: TagOut, 400: ErrorOut, 403: ErrorOut})
def create_tag(request, data: TagCreateIn):
    if not request.user.is_author:
        raise HttpError(403, "Only authors can create tags")

    from blog.models import Tag
    from django.utils.text import slugify

    name = data.name.strip()
    if not name:
        raise HttpError(400, "Tag name cannot be empty")

    tag, created = Tag.objects.get_or_create(
        slug=slugify(name), defaults={"name": name}
    )
    cache.delete("tags:all")
    return 201, TagOut(id=tag.pk, name=tag.name, slug=tag.slug)
