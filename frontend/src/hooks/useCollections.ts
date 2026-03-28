import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Job, PaginatedResponse } from "@/lib/types";

export function useCollections(params: string = "") {
  return useQuery<PaginatedResponse<Job>>({
    queryKey: ["collections", params],
    queryFn: () => api.getCollections(params),
  });
}

export function useCollection(id: number) {
  return useQuery<Job>({
    queryKey: ["collection", id],
    queryFn: () => api.getCollection(id),
    refetchInterval: 5000,
  });
}

export function useLaunchCollection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.launchCollection,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["collections"] }),
  });
}
