from datetime import datetime
from typing import List, Optional
from ninja import Schema


class RegisterIn(Schema):
    email: str
    username: str
    password: str
    role: str = "reader"


class LoginIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    access: str
    refresh: str


class RefreshIn(Schema):
    refresh: str


class AccessTokenOut(Schema):
    access: str


class UserOut(Schema):
    id: int
    email: str
    username: str
    role: str
    bio: str


class TagOut(Schema):
    id: int
    name: str
    slug: str


class AuthorOut(Schema):
    id: int
    username: str
    email: str
    bio: str


class CommentOut(Schema):
    id: int
    author: AuthorOut
    content: str
    created_at: datetime


class PostListOut(Schema):
    id: int
    title: str
    slug: str
    excerpt: str
    author: AuthorOut
    tags: List[TagOut]
    view_count: int
    published_at: Optional[datetime]
    created_at: datetime


class PostDetailOut(Schema):
    id: int
    title: str
    slug: str
    content: str
    excerpt: str
    author: AuthorOut
    tags: List[TagOut]
    status: str
    view_count: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    comments: List[CommentOut]


class PostDraftOut(Schema):
    id: int
    title: str
    slug: str
    status: str
    view_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]


class PostCreateIn(Schema):
    title: str
    content: str
    excerpt: str = ""
    tag_ids: List[int] = []
    status: str = "draft"


class PostUpdateIn(Schema):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    tag_ids: Optional[List[int]] = None


class CommentIn(Schema):
    content: str


class TagCreateIn(Schema):
    name: str


class PaginatedPosts(Schema):
    count: int
    next: Optional[int]
    previous: Optional[int]
    results: List[PostListOut]


class ErrorOut(Schema):
    detail: str
