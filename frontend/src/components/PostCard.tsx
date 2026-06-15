import { Link } from "react-router-dom";
import type { PostSummary } from "../types";

export default function PostCard({ post }: { post: PostSummary }) {
  const date = post.published_at
    ? new Date(post.published_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "";

  return (
    <div className="post-card">
      <Link to={`/posts/${post.slug}`} style={{ display: "block", marginBottom: 6 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text)" }}>{post.title}</h2>
      </Link>
      <p className="text-muted" style={{ fontSize: 13, marginBottom: post.excerpt ? 8 : 10 }}>
        {post.author.username} · {date} · {post.view_count} views
      </p>
      {post.excerpt && (
        <p style={{ color: "#475569", fontSize: 14, marginBottom: 12, lineHeight: 1.6 }}>
          {post.excerpt}
        </p>
      )}
      {post.tags.length > 0 && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {post.tags.map((t) => (
            <Link key={t.slug} to={`/?tag=${t.slug}`} className="tag">{t.name}</Link>
          ))}
        </div>
      )}
    </div>
  );
}
