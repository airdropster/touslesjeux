import { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Download, Search } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

interface GameFiltersProps {
  filters: Record<string, string>;
  onChange: (filters: Record<string, string>) => void;
}

export function GameFilters({ filters, onChange }: GameFiltersProps) {
  const [searchDraft, setSearchDraft] = useState(filters.search ?? "");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync external filter changes into the local draft
  useEffect(() => {
    setSearchDraft(filters.search ?? "");
  }, [filters.search]);

  function handleSearchChange(value: string) {
    setSearchDraft(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      update("search", value);
    }, 300);
  }

  function update(key: string, value: string) {
    const next = { ...filters, [key]: value };
    // Remove empty values to keep URL clean
    if (!value) delete next[key];
    onChange(next);
  }

  async function handleExport() {
    try {
      const params = new URLSearchParams(filters).toString();
      const data = await api.exportGames(params);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "games_export.json";
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Export telecharge");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur lors de l'export");
    }
  }

  return (
    <aside className="w-full space-y-4 lg:w-[280px]">
      <h2 className="text-sm font-medium">Filtres</h2>

      {/* Search */}
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Recherche</label>
        <div className="relative">
          <Search className="absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Titre, designer..."
            value={searchDraft}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-7"
          />
        </div>
      </div>

      {/* Status */}
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Statut</label>
        <Select value={filters.status ?? "all"} onValueChange={(v: string | null) => update("status", v === "all" || v == null ? "" : v)}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Tous" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous</SelectItem>
            <SelectItem value="enriched">Enrichi</SelectItem>
            <SelectItem value="skipped">Ignore</SelectItem>
            <SelectItem value="failed">Echoue</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Complexity range */}
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Complexite (1-10)</label>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            min={1}
            max={10}
            placeholder="Min"
            value={filters.complexity_min ?? ""}
            onChange={(e) => update("complexity_min", e.target.value)}
            className="w-full"
          />
          <span className="text-xs text-muted-foreground">-</span>
          <Input
            type="number"
            min={1}
            max={10}
            placeholder="Max"
            value={filters.complexity_max ?? ""}
            onChange={(e) => update("complexity_max", e.target.value)}
            className="w-full"
          />
        </div>
      </div>

      {/* Player count range */}
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Nombre de joueurs</label>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            min={1}
            placeholder="Min"
            value={filters.min_players ?? ""}
            onChange={(e) => update("min_players", e.target.value)}
            className="w-full"
          />
          <span className="text-xs text-muted-foreground">-</span>
          <Input
            type="number"
            min={1}
            placeholder="Max"
            value={filters.max_players ?? ""}
            onChange={(e) => update("max_players", e.target.value)}
            className="w-full"
          />
        </div>
      </div>

      <Separator />

      {/* Export */}
      <Button variant="outline" className="w-full" onClick={handleExport}>
        <Download className="mr-1.5 size-3.5" />
        Exporter JSON
      </Button>
    </aside>
  );
}
