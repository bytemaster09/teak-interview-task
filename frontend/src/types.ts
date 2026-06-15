export interface User {
  id: number;
  email: string;
  username: string;
  role: "author" | "reader";
  bio: string;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
}

export interface Author {
  id: number;
  username: string;
  email: string;
  bio: string;
}

export interface Comment {
  id: number;
  author: Author;
  content: string;
  created_at: string;
}

export interface PostSummary {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  author: Author;
  tags: Tag[];
  view_count: number;
  published_at: string | null;
  created_at: string;
}

export interface PostDetail extends PostSummary {
  content: string;
  status: string;
  updated_at: string;
  comments: Comment[];
}

export interface DraftPost {
  id: number;
  title: string;
  slug: string;
  status: string;
  view_count: number;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export interface PaginatedPosts {
  count: number;
  next: number | null;
  previous: number | null;
  results: PostSummary[];
}

export interface TokenPair {
  access: string;
  refresh: string;
}
