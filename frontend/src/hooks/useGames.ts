import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Game, GameStats, PaginatedResponse } from "@/lib/types";

export function useGames(params: string = "") {
  return useQuery<PaginatedResponse<Game>>({
    queryKey: ["games", params],
    queryFn: () => api.getGames(params),
  });
}

export function useGame(id: number) {
  return useQuery<Game>({
    queryKey: ["game", id],
    queryFn: () => api.getGame(id),
  });
}

export function useGamesStats() {
  return useQuery<GameStats>({
    queryKey: ["games-stats"],
    queryFn: api.getGamesStats,
  });
}

export function useDeleteGame() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteGame(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["games"] }),
  });
}
