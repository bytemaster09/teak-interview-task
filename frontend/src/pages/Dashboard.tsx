import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDrafts, usePublishPost, useDeletePost } from "../queries/posts";
import Layout from "../components/Layout";
import { useAuth } from "../contexts/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();
  const nav = useNavigate();

  const { data: myPosts, isLoading } = useDrafts();
  const publish = usePublishPost();
  const remove = useDeletePost();

  useEffect(() => {
    if (user && user.role !== "author") nav("/");
  }, [user, nav]);

  async function handleDelete(slug: string) {
    if (!confirm("Delete this post?")) return;
    remove.mutate(slug);
  }

  return (
    <Layout>
      <div className="section-header">
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>My posts</h1>
        <Link to="/dashboard/new" className="btn btn-primary">+ New post</Link>
      </div>

      {isLoading && <p className="spinner">Loading…</p>}

      {!isLoading && myPosts?.length === 0 && (
        <p className="text-muted">
          Nothing here yet.{" "}
          <Link to="/dashboard/new" style={{ color: "var(--text)", fontWeight: 600 }}>
            Write your first post.
          </Link>
        </p>
      )}

      {myPosts?.map((p) => (
        <div key={p.id} className="dash-row">
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <span className={`badge ${p.status === "published" ? "badge-green" : "badge-yellow"}`}>
                {p.status}
              </span>
              <strong style={{ fontSize: 15, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {p.title}
              </strong>
            </div>
            <p className="text-muted" style={{ fontSize: 12 }}>
              Updated {new Date(p.updated_at).toLocaleDateString()} · {p.view_count} views
            </p>
          </div>

          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            <Link to={`/dashboard/edit/${p.slug}`} className="btn btn-outline btn-sm">Edit</Link>

            {p.status === "draft" && (
              <button
                onClick={() => publish.mutate(p.slug)}
                disabled={publish.isPending}
                className="btn btn-outline btn-sm"
              >
                Publish
              </button>
            )}

            {p.status === "published" && (
              <Link to={`/posts/${p.slug}`} target="_blank" rel="noopener" className="btn btn-outline btn-sm">
                View ↗
              </Link>
            )}

            <button
              onClick={() => handleDelete(p.slug)}
              disabled={remove.isPending}
              className="btn btn-danger btn-sm"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </Layout>
  );
}
