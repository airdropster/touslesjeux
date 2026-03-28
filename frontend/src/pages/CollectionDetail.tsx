import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { useCollection } from "@/hooks/useCollections";
import { useSSE } from "@/hooks/useSSE";
import { api } from "@/lib/api";
import { CollectionProgress } from "@/components/CollectionProgress";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CollectionDetail() {
  const { id } = useParams<{ id: string }>();
  const jobId = Number(id);
  const { data: job, isLoading, refetch } = useCollection(jobId);
  const streamUrl = job?.status === "running" ? api.getStreamUrl(jobId) : null;
  const { events } = useSSE(streamUrl);

  async function handleCancel() {
    try {
      await api.cancelCollection(jobId);
      toast.success("Collecte annulee");
      await refetch();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de l'annulation");
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-40 animate-pulse rounded bg-muted" />
      </div>
    );
  }

  if (!job) {
    return <p className="py-8 text-center text-muted-foreground">Collecte introuvable.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Collecte #{job.id}</h1>
        {job.status === "running" && (
          <Button variant="destructive" onClick={handleCancel}>
            Annuler
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Categories</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{job.categories.join(", ")}</p>
        </CardContent>
      </Card>

      <CollectionProgress job={job} events={events} />

      {job.error_message && (
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">Erreur</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-destructive">{job.error_message}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
