import pytest
from ninja.testing import TestClient

from api.router import api

client = TestClient(api)


@pytest.mark.django_db
class TestListPosts:
    def test_returns_only_published(self, published_post, draft_post):
        resp = client.get("/posts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["slug"] == published_post.slug

    def test_pagination(self, author):
        from blog.models import Post
        for i in range(15):
            Post.objects.create(
                author=author, title=f"Post {i}", content="...", status="published"
            )
        resp = client.get("/posts?page=2&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 5
        assert data["previous"] == 1
        assert data["next"] is None

    def test_filter_by_tag(self, published_post, author):
        from blog.models import Post, Tag
        tag = Tag.objects.create(name="python", slug="python")
        published_post.tags.add(tag)

        other = Post.objects.create(
            author=author, title="Other", content="...", status="published"
        )

        resp = client.get("/posts?tag=python")
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["id"] == published_post.pk


@pytest.mark.django_db
class TestGetPost:
    def test_get_published_post(self, published_post):
        resp = client.get(f"/posts/{published_post.slug}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Hello World"
        assert "content" in data
        assert "comments" in data

    def test_draft_not_accessible(self, draft_post):
        resp = client.get(f"/posts/{draft_post.slug}")
        assert resp.status_code == 404

    def test_not_found(self):
        resp = client.get("/posts/nonexistent-slug")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestCreatePost:
    def test_author_can_create(self, author_token):
        resp = client.post(
            "/posts",
            json={"title": "New Post", "content": "Body text here", "status": "draft"},
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert "slug" in data

    def test_reader_cannot_create(self, reader_token):
        resp = client.post(
            "/posts",
            json={"title": "Sneaky Post", "content": "..."},
            headers={"Authorization": f"Bearer {reader_token}"},
        )
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create(self):
        resp = client.post("/posts", json={"title": "Post", "content": "..."})
        assert resp.status_code == 401

    def test_slug_generated_from_title(self, author_token):
        resp = client.post(
            "/posts",
            json={"title": "My First Post!", "content": "Hello."},
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["slug"] == "my-first-post"


@pytest.mark.django_db
class TestPublishPost:
    def test_publish_own_draft(self, draft_post, author_token):
        resp = client.post(
            f"/posts/{draft_post.slug}/publish",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

    def test_cannot_publish_others_post(self, draft_post, reader_token):
        resp = client.post(
            f"/posts/{draft_post.slug}/publish",
            headers={"Authorization": f"Bearer {reader_token}"},
        )
        assert resp.status_code == 403

    def test_idempotent_on_already_published(self, published_post, author_token):
        resp = client.post(
            f"/posts/{published_post.slug}/publish",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"


@pytest.mark.django_db
class TestUpdatePost:
    def test_author_can_update(self, draft_post, author_token):
        resp = client.patch(
            f"/posts/{draft_post.slug}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_cannot_update_others_post(self, draft_post, reader_token):
        resp = client.patch(
            f"/posts/{draft_post.slug}",
            json={"title": "Hacked"},
            headers={"Authorization": f"Bearer {reader_token}"},
        )
        assert resp.status_code == 403


@pytest.mark.django_db
class TestDeletePost:
    def test_author_can_delete(self, draft_post, author_token):
        resp = client.delete(
            f"/posts/{draft_post.slug}",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert resp.status_code == 204

    def test_cannot_delete_others_post(self, draft_post, reader_token):
        resp = client.delete(
            f"/posts/{draft_post.slug}",
            headers={"Authorization": f"Bearer {reader_token}"},
        )
        assert resp.status_code == 403


@pytest.mark.django_db
class TestComments:
    def test_authenticated_user_can_comment(self, published_post, reader_token):
        resp = client.post(
            f"/posts/{published_post.slug}/comments",
            json={"content": "Great post!"},
            headers={"Authorization": f"Bearer {reader_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "Great post!"

    def test_unauthenticated_cannot_comment(self, published_post):
        resp = client.post(
            f"/posts/{published_post.slug}/comments",
            json={"content": "Hello"},
        )
        assert resp.status_code == 401

    def test_comments_on_draft_rejected(self, draft_post, reader_token):
        resp = client.post(
            f"/posts/{draft_post.slug}/comments",
            json={"content": "Comment on draft"},
            headers={"Authorization": f"Bearer {reader_token}"},
        )
        assert resp.status_code == 404

    def test_comments_appear_in_post_detail(self, published_post, reader, reader_token):
        from blog.models import Comment
        Comment.objects.create(post=published_post, author=reader, content="Test comment")
        resp = client.get(f"/posts/{published_post.slug}")
        comments = resp.json()["comments"]
        assert len(comments) == 1
        assert comments[0]["content"] == "Test comment"


@pytest.mark.django_db
class TestDrafts:
    def test_author_sees_all_own_posts(self, author, author_token, published_post, draft_post):
        resp = client.get(
            "/posts/author/drafts",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_reader_cannot_access_drafts(self, reader_token):
        resp = client.get(
            "/posts/author/drafts",
            headers={"Authorization": f"Bearer {reader_token}"},
        )
        assert resp.status_code == 403
