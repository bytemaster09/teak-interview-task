import { QueryClient } from "@tanstack/react-query";

// TTLs mirror the Redis cache TTLs on the backend (settings.py CACHE_TTL_*).
// When a response is still within staleTime the browser serves it instantly
// without a network request — same idea as a CDN edge cache.
const POST_LIST_STALE = 5 * 60 * 1000;   // 5 min
const POST_DETAIL_STALE = 10 * 60 * 1000; // 10 min
const TAGS_STALE = 60 * 60 * 1000;        // 1 hour

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const staleTimes = {
  postList: POST_LIST_STALE,
  postDetail: POST_DETAIL_STALE,
  tags: TAGS_STALE,
};
