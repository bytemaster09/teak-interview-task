import { useSearchParams } from "react-router-dom";
import { usePosts } from "../queries/posts";
import PostCard from "../components/PostCard";
import Layout from "../components/Layout";

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = parseInt(searchParams.get("page") || "1", 10);
  const tag = searchParams.get("tag") || undefined;

  const { data, isLoading, isError, isFetching } = usePosts(page, tag);

  function goToPage(n: number) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("page", String(n));
      return next;
    });
  }

  function clearTag() {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete("tag");
      next.delete("page");
      return next;
    });
  }

  return (
    <Layout>
      {tag && (
        <div style={{ marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
          <span className="text-muted" style={{ fontSize: 14 }}>Tag:</span>
          <strong style={{ fontSize: 14 }}>#{tag}</strong>
          <button onClick={clearTag} className="btn btn-outline btn-sm">✕</button>
        </div>
      )}

      {isError && <p className="error-msg">Failed to load posts.</p>}
      {isLoading && <p className="spinner">Loading…</p>}

      {data && data.results.length === 0 && (
        <p className="text-muted">No posts here yet.</p>
      )}

      <div style={{ opacity: isFetching && !isLoading ? 0.6 : 1, transition: "opacity 0.15s" }}>
        {data?.results.map((p) => <PostCard key={p.id} post={p} />)}
      </div>

      {data && (data.previous || data.next) && (
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
          {data.previous ? (
            <button onClick={() => goToPage(data.previous!)} className="btn btn-outline">
              ← Previous
            </button>
          ) : <span />}
          {data.next && (
            <button onClick={() => goToPage(data.next!)} className="btn btn-outline">
              Next →
            </button>
          )}
        </div>
      )}
    </Layout>
  );
}
