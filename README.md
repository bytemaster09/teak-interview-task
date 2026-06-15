# Blog platform

A full-stack blog application: authors write and publish posts, readers discover and comment on them. Django Ninja on the back end, React + TypeScript on the front end, Redis for caching and async task queuing.

---

## Running it locally

You'll need Python 3.11+ and Node 18+. Redis is optional — the app degrades gracefully without it (falls back to LocMemCache, tasks run synchronously inline).

```bash
# Backend
cd backend
cp ../.env.example .env   # defaults work out of the box for local dev
make setup                 # creates .venv, installs deps, runs migrations
make run                   # → http://localhost:8000/api/docs
```

```bash
# Frontend (separate terminal)
cd frontend
make setup
make dev                   # → http://localhost:5173
```

```bash
# Tests
cd backend && make test

# Create a superuser for the admin panel
cd backend && make superuser
# → http://localhost:8000/admin/
```

To enable Redis-backed caching and async task processing:

```bash
redis-server
# Set CELERY_TASK_ALWAYS_EAGER=False in backend/.env
cd backend && make worker
```

Docker Compose if you prefer:

```bash
cp .env.example .env
docker compose up --build
```

---

## API

Swagger UI lives at **http://localhost:8000/api/docs** — Django Ninja generates it automatically from the route definitions, which is one of its nicest features.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | — | Register as author or reader |
| POST | `/api/auth/login` | — | Get a JWT pair |
| POST | `/api/auth/refresh` | — | Refresh access token |
| GET | `/api/auth/me` | ✓ | Current user |
| GET | `/api/posts` | — | Paginated list (`?page=`, `?tag=`, `?author_id=`) |
| GET | `/api/posts/{slug}` | — | Post detail + comments |
| POST | `/api/posts` | author | Create a post |
| PATCH | `/api/posts/{slug}` | author | Edit a post |
| POST | `/api/posts/{slug}/publish` | author | Publish a draft |
| DELETE | `/api/posts/{slug}` | author | Delete a post |
| GET | `/api/posts/author/drafts` | author | All your posts (any status) |
| POST | `/api/posts/{slug}/comments` | ✓ | Add a comment |
| GET | `/api/tags` | — | All tags |
| POST | `/api/tags` | author | Create a tag |
| GET | `/api/health` | — | Service health check |

---

## Design decisions

**Single User model, role field.** I considered separate Author and Reader models but ruled it out — there's nothing distinct enough between them at this scale to justify the join complexity. A `role` field on a single `AbstractUser` subclass is simpler and trivially extensible. Email is the login identifier (`USERNAME_FIELD = "email"`) because most real users remember their email, not a username.

**Slugs for all post routes.** All single-post operations use `/{slug}` rather than `/{post_id}`. Cleaner shareable URLs, no leaking sequential IDs. I hit an unexpected issue here during testing: Django Ninja's `TestClient` resolves URLs by path before checking HTTP method, so having `GET /{slug}` (str param) alongside `PATCH /{post_id}` (int param) was causing the GET handler to match both. Fixed by unifying all single-post operations on `/{slug}` so Ninja merges them into one URL pattern and dispatches by method.

**Django Ninja over DRF.** Pydantic-native schemas mean no separate serializer layer. You define your shape once and it's validated on the way in and serialized on the way out. The automatic OpenAPI docs are a bonus. I'd reach for DRF on a team that already has DRF conventions and tooling, but for a greenfield API it's harder to justify the extra translation step.

**React Query instead of Redux.** All meaningful state in this app is server state — data from the API, with far more reads than writes. React Query is specifically designed for this. It gives you automatic deduplication, stale-while-revalidate, optimistic cache seeding on mutations (`setQueryData` after a successful update so re-visiting a just-edited post is instant), and a sensible `isPending`/`isError` model for every operation. Redux would add real value if there were significant client state to manage — a shopping cart, real-time notifications across components, complex local UI state. There isn't, so adding it would be engineering for hypothetical future requirements.

**Cache layers in sync.** The `staleTime` values in `src/lib/queryClient.ts` match the Redis TTLs in `settings.py` exactly:

| Data | Redis TTL | React Query staleTime |
|------|-----------|-----------------------|
| Post lists | 5 min | 5 min |
| Post detail | 10 min | 10 min |
| Tags | 1 hr | 1 hr |

Both layers share the same freshness budget. A user who fetched the post list five minutes ago won't trigger a network request until Redis has also expired the entry.

**Cache invalidation via signals.** Post list and detail caches are cleared by Django signals on `post_save` and `post_delete`. For Redis this uses `delete_pattern("post_list:*")`; for the LocMemCache fallback in dev it calls `cache.clear()`. What I didn't cache: draft lists, comment counts, anything user-specific. The cache is for the read-heavy public-facing content, not the author's management views.

**Celery + Redis for async work.** Two background tasks: `increment_view_count` (dequeues per page view instead of writing to the DB on every request) and `notify_post_published` (hooks into the publish lifecycle — in production this would send an email; here it logs). Both retry with exponential-ish backoff. Without Redis, `CELERY_TASK_ALWAYS_EAGER=True` makes tasks synchronous so the app is fully usable without a worker.

**Database indexes.** Composite index on `(status, -published_at)` covers the home feed query exactly. `(author, status)` covers the dashboard. `slug` is indexed individually because every single-post request hits it. `view_count` is deliberately not indexed for ordering — it changes on every view and would constantly invalidate the B-tree. A Redis sorted set is the right answer for a trending-posts feature.

---

## Observability

I added two things here that aren't in the core feature set but matter a lot in practice.

`core/middleware.py` is a request-ID middleware. Every incoming request gets a short UUID (or accepts one via the `X-Request-ID` header from the caller). The ID is logged with the method, path, status, and latency, and echoed back in the response header. The practical value: when something breaks, you can grep the logs for the request ID from the browser's network tab and see exactly what happened, without needing a full distributed tracing setup.

`/api/health` checks that the database connection is alive and the cache can do a read-after-write. Nothing fancy, but these are exactly the two things a load balancer or Kubernetes liveness probe needs to know. Hitting it also shows which cache backend is active, which is useful when you're debugging the Redis-vs-LocMemCache fallback.

### Testing the cache

With Redis running, you can watch what's being cached in real time:

```bash
redis-cli monitor | grep blog

# List all cached keys
redis-cli keys "blog:*"

# Check TTL on a specific post
redis-cli ttl "blog:post:my-post-slug"
```

The timing difference between a cache miss and hit is measurable with curl:

```bash
# First call — hits the database
time curl -s http://localhost:8000/api/posts > /dev/null

# Second call — served from Redis
time curl -s http://localhost:8000/api/posts > /dev/null
```

The health endpoint doubles as a quick sanity check:

```bash
curl http://localhost:8000/api/health
# {"status":"ok","db":"ok","cache":"ok","cache_backend":"RedisCache"}
```

---

## Assumptions

- Roles are set at registration and don't change. A role-change workflow would need business rules I couldn't infer from the spec.
- Comments are auto-approved. The `Comment` model has an `is_approved` field if you want moderation — it's a one-line query change.
- Tokens are stored in `localStorage`. Simpler for a demo; production would use `HttpOnly` cookies to protect against XSS token theft.
- Email delivery is simulated. The Celery publish notification logs to stdout instead of calling an SMTP provider.

---

## How I used AI

I used Claude throughout this. It helped with initial scaffolding, boilerplate (Makefiles, Docker Compose, base schema definitions), and I used it as an async code reviewer after writing key sections.

A few things I caught and fixed that the AI got wrong or missed:

PyJWT 2.x rejects integer `sub` claims — the original JWT encode had `"sub": user_id` where `user_id` is an `int`. Caught it when tests were returning `None` from `jwt.decode` and traced it to `InvalidSubjectError`. The fix is `str(user_id)`.

The signals module was calling `cache.delete("post_list:*")` which deletes a literal key named `"post_list:*"`, not a pattern. Cache was never actually being cleared on post changes. Fixed with `cache.delete_pattern("post_list:*")` for Redis and `cache.clear()` for the LocMemCache fallback.

The Django Ninja TestClient URL dispatch issue described above in the design section — the PATCH route was being shadowed by the GET handler with a string param.

The React pagination bug: `setSearchParams({ page: "2" })` was replacing the entire query string, dropping the `?tag=` param when changing pages. Fixed with a functional update that merges into the existing params.

---

## One thing I'd do differently

**Cursor-based pagination.** The current `?page=N` implementation uses `OFFSET N LIMIT M`, which forces Postgres to scan and skip N rows on every page flip. For tens of thousands of posts this is fine; past that, query time grows linearly with depth. Cursor pagination keyed on `(published_at, id)` keeps every query O(log N). The tradeoff is losing the ability to jump to an arbitrary page — for a blog feed that's actually the correct UX anyway, so it's a net win.

I'd also move tokens to `HttpOnly` cookies and add rate limiting on auth endpoints before calling this production-ready.
