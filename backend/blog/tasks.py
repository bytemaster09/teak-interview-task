import logging
from celery import shared_task
from django.db.models import F

logger = logging.getLogger("blog")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def increment_view_count(self, post_id: int):
    try:
        from blog.models import Post
        Post.objects.filter(pk=post_id).update(view_count=F("view_count") + 1)
    except Exception as exc:
        logger.warning("Failed to increment view count for post %s: %s", post_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_post_published(self, post_id: int):
    """
    In production this would query a subscriptions table and dispatch
    emails via SES / SendGrid. Here we log so the review call can see
    the task firing without an email provider configured.
    """
    try:
        from blog.models import Post
        post = Post.objects.select_related("author").get(pk=post_id)
        logger.info(
            "NOTIFY: post '%s' by %s published — would email subscribers here.",
            post.title,
            post.author.email,
        )
    except Exception as exc:
        logger.error("notify_post_published failed for post %s: %s", post_id, exc)
        raise self.retry(exc=exc)
