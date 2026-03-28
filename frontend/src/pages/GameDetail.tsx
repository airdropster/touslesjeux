import { Link, useNavigate, useParams } from "react-router-dom";
import { useGame, useDeleteGame } from "@/hooks/useGames";
import { api } from "@/lib/api";
import { GameDetail } from "@/components/GameDetail";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ArrowLeft, Pencil, RotateCcw, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useState } from "react";

export default function GameDetailPage() {
  const { id } = useParams<{ id: string }>();
  const gameId = Number(id);
  const navigate = useNavigate();
  const { data: game, isLoading, error, refetch } = useGame(gameId);
  const deleteGame = useDeleteGame();
  const [reprocessing, setReprocessing] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  async function handleReprocess() {
    setReprocessing(true);
    try {
      await api.reprocessGame(gameId);
      toast.success("Jeu envoye pour retraitement");
      await refetch();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors du retraitement");
    } finally {
      setReprocessing(false);
    }
  }

  function handleDelete() {
    deleteGame.mutate(gameId, {
      onSuccess: () => {
        toast.success("Jeu supprime");
        navigate("/games");
      },
      onError: (err) =>
        toast.error(err instanceof Error ? err.message : "Erreur lors de la suppression"),
    });
    setDeleteOpen(false);
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-40 animate-pulse rounded bg-muted" />
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

  const showReprocess = game.status === "skipped" || game.status === "failed";

  return (
    <div className="space-y-4">
      {/* Action bar */}
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="ghost" size="sm" render={<Link to="/games" />}>
          <ArrowLeft className="mr-1 size-3.5" />
          Retour
        </Button>
        <div className="flex-1" />
        {showReprocess && (
          <Button variant="outline" size="sm" disabled={reprocessing} onClick={handleReprocess}>
            <RotateCcw className="mr-1 size-3.5" />
            {reprocessing ? "Retraitement..." : "Retraiter"}
          </Button>
        )}
        <Button variant="outline" size="sm" render={<Link to={`/games/${game.id}/edit`} />}>
          <Pencil className="mr-1 size-3.5" />
          Modifier
        </Button>
        <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
          <DialogTrigger render={<Button variant="destructive" size="sm" />}>
            <Trash2 className="mr-1 size-3.5" />
            Supprimer
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Supprimer le jeu</DialogTitle>
              <DialogDescription>
                Voulez-vous vraiment supprimer "{game.title}" ? Cette action est irreversible.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <DialogClose render={<Button variant="outline" />}>Annuler</DialogClose>
              <Button
                variant="destructive"
                disabled={deleteGame.isPending}
                onClick={handleDelete}
              >
                {deleteGame.isPending ? "Suppression..." : "Supprimer"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <GameDetail game={game} />
    </div>
  );
}
