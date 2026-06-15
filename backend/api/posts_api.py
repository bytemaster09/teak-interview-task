from typing import List, Optional

from django.core.cache import cache
from django.conf import settings
from django.db.models import Prefetch
from ninja import Query, Router
from ninja.errors import HttpError
from ninja.responses import Status

from .auth import jwt_auth
from .schemas import (
    AuthorOut,
    CommentIn,
    CommentOut,
    ErrorOut,
    PaginatedPosts,
    PostCreateIn,
    PostDetailOut,
    PostDraftOut,
    PostListOut,
    PostUpdateIn,
    TagCreateIn,
    TagOut,
)

router = Router(tags=["posts"])


def _post_to_list_out(post) -> PostListOut:
    return PostListOut(
        id=post.pk,
        title=post.title,
        slug=post.slug,
        excerpt=post.excerpt,
        author=AuthorOut(
            id=post.author.pk,
            username=post.author.username,
            email=post.author.email,
            bio=post.author.bio,
        ),
        tags=[TagOut(id=t.pk, name=t.name, slug=t.slug) for t in post.tags.all()],
        view_count=post.view_count,
        published_at=post.published_at,
        created_at=post.created_at,
    )


def _post_qs():
    from blog.models import Post
    return (
        Post.objects.select_related("author")
        .prefetch_related("tags", Prefetch("comments", queryset=_comment_qs()))
    )


def _comment_qs():
    from blog.models import Comment
    return Comment.objects.select_related("author")


@router.get("", response=PaginatedPosts)
def list_posts(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    tag: Optional[str] = None,
    author_id: Optional[int] = None,
):
    from blog.models import Post

    cache_key = f"post_list:p{page}:ps{page_size}:t{tag}:a{author_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    qs = _post_qs().filter(status=Post.Status.PUBLISHED)
    if tag:
        qs = qs.filter(tags__slug=tag)
    if author_id:
        qs = qs.filter(author_id=author_id)

    total = qs.count()
    offset = (page - 1) * page_size
    posts = qs[offset: offset + page_size]

    result = PaginatedPosts(
        count=total,
        next=page + 1 if offset + page_size < total else None,
        previous=page - 1 if page > 1 else None,
        results=[_post_to_list_out(p) for p in posts],
    )
    cache.set(cache_key, result, settings.CACHE_TTL_POST_LIST)
    return result


@router.get("/{slug}", response={200: PostDetailOut, 404: ErrorOut})
def get_post(request, slug: str):
    from blog.models import Post
    from blog.tasks import increment_view_count

    cache_key = f"post:{slug}"
    cached = cache.get(cache_key)
    if cached:
        increment_view_count.delay(cached.id)
        return cached

    try:
        post = _post_qs().get(slug=slug, status=Post.Status.PUBLISHED)
    except Post.DoesNotExist:
        raise HttpError(404, "Post not found")

    result = PostDetailOut(
        id=post.pk,
        title=post.title,
        slug=post.slug,
        content=post.content,
        excerpt=post.excerpt,
        author=AuthorOut(
            id=post.author.pk,
            username=post.author.username,
            email=post.author.email,
            bio=post.author.bio,
        ),
        tags=[TagOut(id=t.pk, name=t.name, slug=t.slug) for t in post.tags.all()],
        status=post.status,
        view_count=post.view_count,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        comments=[
            CommentOut(
                id=c.pk,
                author=AuthorOut(
                    id=c.author.pk,
                    username=c.author.username,
                    email=c.author.email,
                    bio=c.author.bio,
                ),
                content=c.content,
                created_at=c.created_at,
            )
            for c in post.comments.all()
        ],
    )
    cache.set(cache_key, result, settings.CACHE_TTL_POST_DETAIL)
    increment_view_count.delay(post.pk)
    return result


@router.post("", auth=jwt_auth, response={201: PostDetailOut, 403: ErrorOut})
def create_post(request, data: PostCreateIn):
    from blog.models import Post, Tag

    if not request.user.is_author:
        raise HttpError(403, "Only authors can create posts")

    if data.status not in (Post.Status.DRAFT, Post.Status.PUBLISHED):
        raise HttpError(400, "status must be 'draft' or 'published'")

    tags = list(Tag.objects.filter(pk__in=data.tag_ids))
    post = Post.objects.create(
        author=request.user,
        title=data.title,
        content=data.content,
        excerpt=data.excerpt,
        status=data.status,
    )
    if tags:
        post.tags.set(tags)

    if post.status == Post.Status.PUBLISHED:
        from blog.tasks import notify_post_published
        notify_post_published.delay(post.pk)

    post.refresh_from_db()
    return Status(201, _build_detail(post))


@router.patch("/{slug}", auth=jwt_auth, response={200: PostDetailOut, 403: ErrorOut, 404: ErrorOut})
def update_post(request, slug: str, data: PostUpdateIn):
    from blog.models import Post, Tag

    try:
        post = Post.objects.select_related("author").prefetch_related("tags").get(slug=slug)
    except Post.DoesNotExist:
        raise HttpError(404, "Post not found")

    if post.author_id != request.user.pk:
        raise HttpError(403, "You can only edit your own posts")

    if data.title is not None:
        post.title = data.title
        post.slug = ""
    if data.content is not None:
        post.content = data.content
    if data.excerpt is not None:
        post.excerpt = data.excerpt

    post.save()

    if data.tag_ids is not None:
        post.tags.set(Tag.objects.filter(pk__in=data.tag_ids))

    post.refresh_from_db()
    return _build_detail(post)


@router.post("/{slug}/publish", auth=jwt_auth, response={200: PostDetailOut, 403: ErrorOut, 404: ErrorOut})
def publish_post(request, slug: str):
    from blog.models import Post
    from blog.tasks import notify_post_published

    try:
        post = Post.objects.select_related("author").prefetch_related("tags").get(slug=slug)
    except Post.DoesNotExist:
        raise HttpError(404, "Post not found")

    if post.author_id != request.user.pk:
        raise HttpError(403, "You can only publish your own posts")

    if post.status == Post.Status.PUBLISHED:
        return _build_detail(post)

    post.status = Post.Status.PUBLISHED
    post.save()
    notify_post_published.delay(post.pk)
    post.refresh_from_db()
    return _build_detail(post)


@router.delete("/{slug}", auth=jwt_auth, response={204: None, 403: ErrorOut, 404: ErrorOut})
def delete_post(request, slug: str):
    from blog.models import Post

    try:
        post = Post.objects.get(slug=slug)
    except Post.DoesNotExist:
        raise HttpError(404, "Post not found")

    if post.author_id != request.user.pk:
        raise HttpError(403, "You can only delete your own posts")

    post.delete()
    return Status(204, None)


@router.post("/{slug}/comments", auth=jwt_auth, response={201: CommentOut, 404: ErrorOut})
def add_comment(request, slug: str, data: CommentIn):
    from blog.models import Post, Comment

    try:
        post = Post.objects.get(slug=slug, status=Post.Status.PUBLISHED)
    except Post.DoesNotExist:
        raise HttpError(404, "Post not found")

    comment = Comment.objects.create(post=post, author=request.user, content=data.content)
    cache.delete(f"post:{post.slug}")

    return Status(201, CommentOut(
        id=comment.pk,
        author=AuthorOut(
            id=request.user.pk,
            username=request.user.username,
            email=request.user.email,
            bio=request.user.bio,
        ),
        content=comment.content,
        created_at=comment.created_at,
    ))


@router.get("/author/drafts", auth=jwt_auth, response={200: List[PostDraftOut], 403: ErrorOut})
def my_drafts(request):
    from blog.models import Post

    if not request.user.is_author:
        raise HttpError(403, "Authors only")

    posts = Post.objects.filter(author=request.user).order_by("-created_at")
    return [
        PostDraftOut(
            id=p.pk,
            title=p.title,
            slug=p.slug,
            status=p.status,
            view_count=p.view_count,
            created_at=p.created_at,
            updated_at=p.updated_at,
            published_at=p.published_at,
        )
        for p in posts
    ]


def _build_detail(post) -> PostDetailOut:
    from blog.models import Comment
    comments = (
        Comment.objects.filter(post=post)
        .select_related("author")
        .order_by("created_at")
    )
    return PostDetailOut(
        id=post.pk,
        title=post.title,
        slug=post.slug,
        content=post.content,
        excerpt=post.excerpt,
        author=AuthorOut(
            id=post.author.pk,
            username=post.author.username,
            email=post.author.email,
            bio=post.author.bio,
        ),
        tags=[TagOut(id=t.pk, name=t.name, slug=t.slug) for t in post.tags.all()],
        status=post.status,
        view_count=post.view_count,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        comments=[
            CommentOut(
                id=c.pk,
                author=AuthorOut(
                    id=c.author.pk,
                    username=c.author.username,
                    email=c.author.email,
                    bio=c.author.bio,
                ),
                content=c.content,
                created_at=c.created_at,
            )
            for c in comments
        ],
    )
