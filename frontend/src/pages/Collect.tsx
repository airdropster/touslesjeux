import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useLaunchCollection } from "@/hooks/useCollections";
import { CategorySelector } from "@/components/CategorySelector";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";

export default function Collect() {
  const [categories, setCategories] = useState<string[]>([]);
  const [targetCount, setTargetCount] = useState(100);
  const navigate = useNavigate();
  const launch = useLaunchCollection();

  function handleLaunch() {
    if (categories.length === 0) {
      toast.error("Ajoutez au moins une categorie");
      return;
    }

    launch.mutate(
      { categories, target_count: targetCount },
      {
        onSuccess: (data: { id: number }) => {
          toast.success("Collecte lancee");
          navigate(`/collections/${data.id}`);
        },
        onError: (err: Error) => {
          toast.error(err.message || "Erreur lors du lancement");
        },
      }
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Nouvelle collecte</h1>

      <Card>
        <CardHeader>
          <CardTitle>Categories</CardTitle>
        </CardHeader>
        <CardContent>
          <CategorySelector categories={categories} onChange={setCategories} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Nombre de jeux cible: {targetCount}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Slider
            value={[targetCount]}
            onValueChange={(val) => setTargetCount(Array.isArray(val) ? val[0] : val)}
            min={10}
            max={200}
            step={10}
          />
          <div className="mt-2 flex justify-between text-xs text-muted-foreground">
            <span>10</span>
            <span>200</span>
          </div>
        </CardContent>
      </Card>

      <Button
        size="lg"
        onClick={handleLaunch}
        disabled={launch.isPending || categories.length === 0}
      >
        {launch.isPending ? "Lancement..." : "Lancer la collecte"}
      </Button>
    </div>
  );
}
