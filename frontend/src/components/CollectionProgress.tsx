import type { Job } from "@/lib/types";
import type { SSEEvent } from "@/hooks/useSSE";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Re-export the SSEEvent type used in the hook for convenience
export type { SSEEvent };

interface CollectionProgressProps {
  job: Job;
  events: SSEEvent[];
}

const statusConfig: Record<Job["status"], { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  pending: { label: "En attente", variant: "outline" },
  running: { label: "En cours", variant: "default" },
  completed: { label: "Termine", variant: "secondary" },
  failed: { label: "Echoue", variant: "destructive" },
  cancelled: { label: "Annule", variant: "outline" },
};

export function CollectionProgress({ job, events }: CollectionProgressProps) {
  const processed = job.processed_count + job.skipped_count + job.failed_count;
  const percentage = job.target_count > 0 ? Math.min(100, Math.round((processed / job.target_count) * 100)) : 0;

  const gamesAdded = events
    .filter((e) => e.event === "game_added")
    .map((e) => e.data as { title: string });

  const { label, variant } = statusConfig[job.status];

  return (
    <div className="space-y-4">
      {/* Status and progress */}
      <div className="flex items-center gap-3">
        <Badge variant={variant}>{label}</Badge>
        <span className="text-sm text-muted-foreground">
          {processed} / {job.target_count}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Counters */}
      <div className="flex gap-4 text-sm">
        <span className="text-green-600">Enrichis: {job.processed_count}</span>
        <span className="text-yellow-600">Ignores: {job.skipped_count}</span>
        <span className="text-red-600">Echoues: {job.failed_count}</span>
      </div>

      {/* Games added in real-time */}
      {gamesAdded.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Jeux ajoutes ({gamesAdded.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm">
              {gamesAdded.map((game, i) => (
                <li key={i} className="text-muted-foreground">
                  {game.title}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
