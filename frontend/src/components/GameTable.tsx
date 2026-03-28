import { useState } from "react";
import { Link } from "react-router-dom";
import type { Game } from "@/lib/types";
import { useDeleteGame } from "@/hooks/useGames";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
import { ArrowUpDown, Eye, Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";

type SortKey = "title" | "year" | "designer" | "complexity_score" | "status";
type SortDir = "asc" | "desc";

interface GameTableProps {
  games: Game[];
}

const statusConfig: Record<
  Game["status"],
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  enriched: { label: "Enrichi", variant: "default" },
  skipped: { label: "Ignore", variant: "secondary" },
  failed: { label: "Echoue", variant: "destructive" },
};

export function GameTable({ games }: GameTableProps) {
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const deleteGame = useDeleteGame();

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function handleDelete(id: number) {
    deleteGame.mutate(id, {
      onSuccess: () => toast.success("Jeu supprime"),
      onError: (err) =>
        toast.error(err instanceof Error ? err.message : "Erreur lors de la suppression"),
    });
  }

  const sorted = [...games].sort((a, b) => {
    if (!sortKey) return 0;
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    if (aVal == null && bVal == null) return 0;
    if (aVal == null) return 1;
    if (bVal == null) return -1;
    const cmp = typeof aVal === "string" ? aVal.localeCompare(String(bVal)) : Number(aVal) - Number(bVal);
    return sortDir === "asc" ? cmp : -cmp;
  });

  const columns: { key: SortKey; label: string }[] = [
    { key: "title", label: "Titre" },
    { key: "year", label: "Annee" },
    { key: "designer", label: "Designer" },
    { key: "complexity_score", label: "Complexite" },
    { key: "status", label: "Statut" },
  ];

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((col) => (
            <TableHead key={col.key}>
              <button
                type="button"
                className="inline-flex items-center gap-1 hover:text-foreground"
                onClick={() => handleSort(col.key)}
              >
                {col.label}
                <ArrowUpDown className="size-3" />
              </button>
            </TableHead>
          ))}
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sorted.length === 0 ? (
          <TableRow>
            <TableCell colSpan={6} className="text-center text-muted-foreground">
              Aucun jeu trouve.
            </TableCell>
          </TableRow>
        ) : (
          sorted.map((game) => {
            const cfg = statusConfig[game.status];
            return (
              <TableRow key={game.id}>
                <TableCell className="font-medium max-w-[250px] truncate">
                  {game.title}
                </TableCell>
                <TableCell>{game.year ?? "-"}</TableCell>
                <TableCell className="max-w-[200px] truncate">
                  {game.designer ?? "-"}
                </TableCell>
                <TableCell>
                  {game.complexity_score != null ? `${game.complexity_score}/10` : "-"}
                </TableCell>
                <TableCell>
                  <Badge variant={cfg.variant}>{cfg.label}</Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon-xs" render={<Link to={`/games/${game.id}`} />}>
                      <Eye />
                    </Button>
                    <Button variant="ghost" size="icon-xs" render={<Link to={`/games/${game.id}/edit`} />}>
                      <Pencil />
                    </Button>
                    <DeleteDialog
                      gameTitle={game.title}
                      onConfirm={() => handleDelete(game.id)}
                      isLoading={deleteGame.isPending}
                    />
                  </div>
                </TableCell>
              </TableRow>
            );
          })
        )}
      </TableBody>
    </Table>
  );
}

function DeleteDialog({
  gameTitle,
  onConfirm,
  isLoading,
}: {
  gameTitle: string;
  onConfirm: () => void;
  isLoading: boolean;
}) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="ghost" size="icon-xs" />}>
        <Trash2 className="text-destructive" />
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Supprimer le jeu</DialogTitle>
          <DialogDescription>
            Voulez-vous vraiment supprimer "{gameTitle}" ? Cette action est irreversible.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Annuler</DialogClose>
          <Button
            variant="destructive"
            disabled={isLoading}
            onClick={() => {
              onConfirm();
              setOpen(false);
            }}
          >
            {isLoading ? "Suppression..." : "Supprimer"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
