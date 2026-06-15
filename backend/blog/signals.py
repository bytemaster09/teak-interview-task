import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Post

logger = logging.getLogger("blog")


def _clear_post_list_cache():
    # django-redis exposes delete_pattern; LocMemCache falls back to full clear.
    # Full clear is fine for dev — the list cache is cheap to rebuild.
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern("post_list:*")
    else:
        cache.clear()


@receiver(post_save, sender=Post)
def on_post_save(sender, instance, **kwargs):
    cache.delete(f"post:{instance.slug}")
    _clear_post_list_cache()
    logger.debug("Cache invalidated for post '%s'", instance.slug)


@receiver(post_delete, sender=Post)
def on_post_delete(sender, instance, **kwargs):
    cache.delete(f"post:{instance.slug}")
    _clear_post_list_cache()
