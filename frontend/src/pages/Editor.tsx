import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useCreatePost, useUpdatePost, usePublishPost, usePost } from "../queries/posts";
import { useTags, useCreateTag } from "../queries/tags";
import Layout from "../components/Layout";
import { useAuth } from "../contexts/AuthContext";

export default function Editor() {
  const { slug } = useParams<{ slug?: string }>();
  const isEdit = Boolean(slug);
  const { user } = useAuth();
  const nav = useNavigate();

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [excerpt, setExcerpt] = useState("");
  const [selectedTags, setSelectedTags] = useState<number[]>([]);
  const [newTag, setNewTag] = useState("");

  const { data: existingPost } = usePost(slug ?? "");
  const { data: allTags = [] } = useTags();

  const createPost = useCreatePost();
  const updatePost = useUpdatePost();
  const publishPost = usePublishPost();
  const createTag = useCreateTag();

  useEffect(() => {
    if (user && user.role !== "author") nav("/");
  }, [user, nav]);

  useEffect(() => {
    if (existingPost) {
      setTitle(existingPost.title);
      setContent(existingPost.content);
      setExcerpt(existingPost.excerpt);
      setSelectedTags(existingPost.tags.map((t) => t.id));
    }
  }, [existingPost]);

  const isBusy = createPost.isPending || updatePost.isPending || publishPost.isPending;
  const error =
    (createPost.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
    (updatePost.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
    null;

  async function save(publish: boolean) {
    if (isEdit && slug) {
      await updatePost.mutateAsync({ slug, data: { title, content, excerpt, tag_ids: selectedTags } });
      if (publish) await publishPost.mutateAsync(slug);
    } else {
      await createPost.mutateAsync({
        title,
        content,
        excerpt,
        tag_ids: selectedTags,
        status: publish ? "published" : "draft",
      });
    }
    nav("/dashboard");
  }

  async function addNewTag() {
    if (!newTag.trim()) return;
    const tag = await createTag.mutateAsync(newTag.trim());
    setSelectedTags((prev) => [...prev, tag.id]);
    setNewTag("");
  }

  function toggleTag(id: number) {
    setSelectedTags((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  }

  return (
    <Layout>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>
        {isEdit ? "Edit post" : "New post"}
      </h1>

      {error && <p className="error-msg">{error}</p>}

      <div className="card" style={{ padding: "1.5rem" }}>
        <div className="field">
          <label className="label">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Your post title"
            className="input"
          />
        </div>

        <div className="field">
          <label className="label">Excerpt</label>
          <input
            type="text"
            value={excerpt}
            onChange={(e) => setExcerpt(e.target.value)}
            placeholder="Short summary shown in listings (optional)"
            className="input"
          />
        </div>

        <div className="field">
          <label className="label">Content</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your post…"
            rows={14}
            className="input"
            style={{ minHeight: 280 }}
          />
        </div>

        <div className="field">
          <label className="label">Tags</label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8, marginBottom: 12 }}>
            {allTags.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => toggleTag(t.id)}
                className={`tag-chip${selectedTags.includes(t.id) ? " selected" : ""}`}
              >
                {t.name}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              placeholder="New tag…"
              className="input"
              style={{ flex: 1 }}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addNewTag())}
            />
            <button
              type="button"
              onClick={addNewTag}
              disabled={createTag.isPending}
              className="btn btn-outline"
            >
              Add
            </button>
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, marginTop: 4 }}>
          <button
            type="button"
            onClick={() => save(false)}
            disabled={isBusy || !title.trim()}
            className="btn btn-outline"
          >
            Save draft
          </button>
          <button
            type="button"
            onClick={() => save(true)}
            disabled={isBusy || !title.trim() || !content.trim()}
            className="btn btn-primary"
          >
            {isBusy ? "Saving…" : isEdit ? "Save & publish" : "Publish"}
          </button>
        </div>
      </div>
    </Layout>
  );
}
