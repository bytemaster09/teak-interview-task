import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { tags as tagsApi } from "../api";
import { staleTimes } from "../lib/queryClient";

export const tagKeys = {
  all: ["tags"] as const,
};

export function useTags() {
  return useQuery({
    queryKey: tagKeys.all,
    queryFn: () => tagsApi.list().then((r) => r.data),
    staleTime: staleTimes.tags,
  });
}

export function useCreateTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => tagsApi.create(name).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tagKeys.all });
    },
  });
}
