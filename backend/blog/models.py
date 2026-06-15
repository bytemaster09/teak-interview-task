from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="posts",
        limit_choices_to={"role": "author"},
    )
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True, db_index=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True, max_length=500)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    view_count = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["author", "status"]),
        ]
        ordering = ["-published_at", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug(slugify(self.title))
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def _unique_slug(self, base: str) -> str:
        slug, n = base, 1
        while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["post", "created_at"])]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} on '{self.post}'"
