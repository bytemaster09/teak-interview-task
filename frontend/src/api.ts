import axios from "axios";
import type { PaginatedPosts, PostDetail, PostSummary, Tag, TokenPair, User, DraftPost, Comment } from "./types";

const http = axios.create({ baseURL: "/api" });

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

http.interceptors.response.use(
  (r) => r,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post<{ access: string }>("/api/auth/refresh", { refresh });
          localStorage.setItem("access_token", data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return http(original);
        } catch (refreshErr) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
          return Promise.reject(refreshErr);
        }
      }
    }
    return Promise.reject(err);
  }
);

export const auth = {
  register: (email: string, username: string, password: string, role: string) =>
    http.post<TokenPair>("/auth/register", { email, username, password, role }),
  login: (email: string, password: string) =>
    http.post<TokenPair>("/auth/login", { email, password }),
  me: () => http.get<User>("/auth/me"),
};

export const posts = {
  list: (page = 1, tag?: string, authorId?: number) =>
    http.get<PaginatedPosts>("/posts", { params: { page, ...(tag && { tag }), ...(authorId && { author_id: authorId }) } }),
  get: (slug: string) => http.get<PostDetail>(`/posts/${slug}`),
  create: (data: { title: string; content: string; excerpt: string; tag_ids: number[]; status: string }) =>
    http.post<PostDetail>("/posts", data),
  update: (slug: string, data: { title?: string; content?: string; excerpt?: string; tag_ids?: number[] }) =>
    http.patch<PostDetail>(`/posts/${slug}`, data),
  publish: (slug: string) => http.post<PostDetail>(`/posts/${slug}/publish`),
  delete: (slug: string) => http.delete(`/posts/${slug}`),
  drafts: () => http.get<DraftPost[]>("/posts/author/drafts"),
  comment: (slug: string, content: string) =>
    http.post<Comment>(`/posts/${slug}/comments`, { content }),
};

export const tags = {
  list: () => http.get<Tag[]>("/tags"),
  create: (name: string) => http.post<Tag>("/tags", { name }),
};
