import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { usePost, useAddComment } from "../queries/posts";
import Layout from "../components/Layout";
import { useAuth } from "../contexts/AuthContext";

export default function PostDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();

  const { data: post, isLoading, isError } = usePost(slug ?? "");
  const addComment = useAddComment(slug ?? "");
  const [draft, setDraft] = useState("");

  async function submitComment(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim()) return;
    await addComment.mutateAsync(draft.trim());
    setDraft("");
  }

  if (isLoading) return <Layout><p className="spinner">Loading…</p></Layout>;
  if (isError || !post) return <Layout><p>Post not found.</p></Layout>;

  const date = post.published_at
    ? new Date(post.published_at).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : "";

  return (
    <Layout>
      <article>
        <h1 className="article-title">{post.title}</h1>
        <p className="article-meta">
          {post.author.username} · {date} · {post.view_count} views
        </p>

        {post.tags.length > 0 && (
          <div className="tag-row">
            {post.tags.map((t) => (
              <Link key={t.slug} to={`/?tag=${t.slug}`} className="tag">
                {t.name}
              </Link>
            ))}
          </div>
        )}

        <div className="article-body">{post.content}</div>

        <hr className="divider" />

        <section>
          <h3 style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>
            {post.comments.length === 0
              ? "No comments yet"
              : `${post.comments.length} comment${post.comments.length === 1 ? "" : "s"}`}
          </h3>

          {post.comments.map((c) => (
            <div key={c.id} className="comment">
              <p style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{c.author.username}</p>
              <p style={{ fontSize: 14, color: "#374151" }}>{c.content}</p>
              <p className="text-muted" style={{ fontSize: 12, marginTop: 6 }}>
                {new Date(c.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}

          {user ? (
            <form onSubmit={submitComment} style={{ marginTop: 20 }}>
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Write a comment…"
                rows={3}
                className="input"
                style={{ marginBottom: 8 }}
              />
              <button
                type="submit"
                disabled={addComment.isPending || !draft.trim()}
                className="btn btn-primary"
              >
                {addComment.isPending ? "Posting…" : "Post comment"}
              </button>
              {addComment.isError && (
                <p className="error-msg" style={{ marginTop: 6 }}>
                  Failed to post comment — try again.
                </p>
              )}
            </form>
          ) : (
            <p className="text-muted" style={{ fontSize: 14, marginTop: 16 }}>
              <Link to="/login" style={{ color: "var(--text)", fontWeight: 600 }}>Sign in</Link>{" "}
              to leave a comment.
            </p>
          )}
        </section>
      </article>
    </Layout>
  );
}
