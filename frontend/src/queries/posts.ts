import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { posts as postsApi } from "../api";
import { staleTimes } from "../lib/queryClient";
import type { PostDetail } from "../types";

// Structured key factory keeps cache invalidation predictable — a pattern
// from the React Query docs that pays off once mutations start invalidating lists.
export const postKeys = {
  all: ["posts"] as const,
  lists: () => [...postKeys.all, "list"] as const,
  list: (page: number, tag?: string, authorId?: number) =>
    [...postKeys.lists(), { page, tag, authorId }] as const,
  detail: (slug: string) => [...postKeys.all, "detail", slug] as const,
  drafts: () => [...postKeys.all, "drafts"] as const,
};

export function usePosts(page: number, tag?: string, authorId?: number) {
  return useQuery({
    queryKey: postKeys.list(page, tag, authorId),
    queryFn: () => postsApi.list(page, tag, authorId).then((r) => r.data),
    staleTime: staleTimes.postList,
    // keeps the current page visible while the next one loads (smooth pagination)
    placeholderData: keepPreviousData,
  });
}

export function usePost(slug: string) {
  return useQuery({
    queryKey: postKeys.detail(slug),
    queryFn: () => postsApi.get(slug).then((r) => r.data),
    staleTime: staleTimes.postDetail,
    enabled: Boolean(slug),
  });
}

export function useDrafts() {
  return useQuery({
    queryKey: postKeys.drafts(),
    queryFn: () => postsApi.drafts().then((r) => r.data),
    // drafts are the author's own content — always fetch fresh
    staleTime: 0,
  });
}

export function useCreatePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: postsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: postKeys.lists() });
      qc.invalidateQueries({ queryKey: postKeys.drafts() });
    },
  });
}

export function useUpdatePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, data }: { slug: string; data: Parameters<typeof postsApi.update>[1] }) =>
      postsApi.update(slug, data).then((r) => r.data),
    onSuccess: (updated: PostDetail) => {
      qc.invalidateQueries({ queryKey: postKeys.lists() });
      qc.invalidateQueries({ queryKey: postKeys.drafts() });
      // Seed the detail cache with the fresh response so re-visiting the post
      // doesn't trigger another network hit immediately after editing.
      qc.setQueryData(postKeys.detail(updated.slug), updated);
    },
  });
}

export function usePublishPost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => postsApi.publish(slug).then((r) => r.data),
    onSuccess: (published: PostDetail) => {
      qc.invalidateQueries({ queryKey: postKeys.lists() });
      qc.invalidateQueries({ queryKey: postKeys.drafts() });
      qc.setQueryData(postKeys.detail(published.slug), published);
    },
  });
}

export function useDeletePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => postsApi.delete(slug),
    onSuccess: (_data, slug) => {
      qc.removeQueries({ queryKey: postKeys.detail(slug) });
      qc.invalidateQueries({ queryKey: postKeys.lists() });
      qc.invalidateQueries({ queryKey: postKeys.drafts() });
    },
  });
}

export function useAddComment(postSlug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => postsApi.comment(postSlug, content).then((r) => r.data),
    onSuccess: () => {
      // Refetch detail so the comment list is authoritative from the server
      qc.invalidateQueries({ queryKey: postKeys.detail(postSlug) });
    },
  });
}
