import { Link } from "react-router-dom";
import { useGamesStats } from "@/hooks/useGames";
import { useCollections } from "@/hooks/useCollections";
import { StatsCards } from "@/components/StatsCards";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "outline",
  running: "default",
  completed: "secondary",
  failed: "destructive",
  cancelled: "outline",
};

const statusLabel: Record<string, string> = {
  pending: "En attente",
  running: "En cours",
  completed: "Termine",
  failed: "Echoue",
  cancelled: "Annule",
};

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useGamesStats();
  const { data: collections, isLoading: collectionsLoading } = useCollections("per_page=5");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Tableau de bord</h1>
        <Button render={<Link to="/collect" />}>Nouvelle collecte</Button>
      </div>

      {/* Stats */}
      <StatsCards stats={statsLoading ? undefined : stats} />

      {/* Recent collections */}
      <Card>
        <CardHeader>
          <CardTitle>Collectes recentes</CardTitle>
        </CardHeader>
        <CardContent>
          {collectionsLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }, (_, i) => (
                <div key={i} className="h-10 animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : collections?.items.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aucune collecte pour le moment.</p>
          ) : (
            <ul className="space-y-2">
              {collections?.items.map((job) => (
                <li key={job.id}>
                  <Link
                    to={`/collections/${job.id}`}
                    className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant={statusVariant[job.status] ?? "outline"}>
                        {statusLabel[job.status] ?? job.status}
                      </Badge>
                      <span className="text-sm">{job.categories.join(", ")}</span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {job.processed_count + job.skipped_count + job.failed_count} / {job.target_count}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
