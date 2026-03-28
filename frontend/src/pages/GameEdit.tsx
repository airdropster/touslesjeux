import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useGame } from "@/hooks/useGames";
import { api } from "@/lib/api";
import { GameForm } from "@/components/GameForm";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";

export default function GameEdit() {
  const { id } = useParams<{ id: string }>();
  const gameId = Number(id);
  const navigate = useNavigate();
  const { data: game, isLoading, error } = useGame(gameId);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(data: Record<string, unknown>) {
    setSaving(true);
    try {
      await api.updateGame(gameId, data);
      toast.success("Jeu mis a jour");
      navigate(`/games/${gameId}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-96 animate-pulse rounded bg-muted" />
      </div>
    );
  }

  if (error || !game) {
    return (
      <div className="py-8 text-center">
        <p className="text-muted-foreground">
          {error instanceof Error ? error.message : "Jeu introuvable."}
        </p>
        <Button variant="outline" className="mt-4" render={<Link to="/games" />}>
          Retour a la liste
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" render={<Link to={`/games/${gameId}`} />}>
          <ArrowLeft className="mr-1 size-3.5" />
          Retour
        </Button>
        <h1 className="text-2xl font-bold">Modifier: {game.title}</h1>
      </div>

      <GameForm
        game={game}
        onSubmit={handleSubmit}
        isLoading={saving}
        onCancel={() => navigate(`/games/${gameId}`)}
      />
    </div>
  );
}
