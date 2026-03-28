import { useSearchParams } from "react-router-dom";
import { useGames } from "@/hooks/useGames";
import { GameTable } from "@/components/GameTable";
import { GameFilters } from "@/components/GameFilters";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChevronLeft, ChevronRight } from "lucide-react";

const PER_PAGE_OPTIONS = ["10", "20", "50"];

export default function GameList() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Build filters object from URL search params
  const filters: Record<string, string> = {};
  searchParams.forEach((value, key) => {
    if (key !== "page" && key !== "per_page") {
      filters[key] = value;
    }
  });

  const page = Number(searchParams.get("page") ?? "1");
  const perPage = searchParams.get("per_page") ?? "20";

  // Build query params string for the API
  const params = new URLSearchParams(filters);
  params.set("page", String(page));
  params.set("per_page", perPage);

  const { data, isLoading } = useGames(params.toString());

  function handleFiltersChange(next: Record<string, string>) {
    const sp = new URLSearchParams(next);
    sp.set("page", "1"); // Reset to page 1 on filter change
    sp.set("per_page", perPage);
    setSearchParams(sp);
  }

  function handlePageChange(newPage: number) {
    const sp = new URLSearchParams(searchParams);
    sp.set("page", String(newPage));
    setSearchParams(sp);
  }

  function handlePerPageChange(value: string | null) {
    if (!value) return;
    const sp = new URLSearchParams(searchParams);
    sp.set("per_page", value);
    sp.set("page", "1");
    setSearchParams(sp);
  }

  const totalPages = data?.pages ?? 1;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Jeux</h1>

      <div className="flex flex-col gap-4 lg:flex-row">
        {/* Filters sidebar */}
        <GameFilters filters={filters} onChange={handleFiltersChange} />

        {/* Main table area */}
        <div className="min-w-0 flex-1 space-y-4">
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }, (_, i) => (
                <div key={i} className="h-10 animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : (
            <>
              <GameTable games={data?.items ?? []} />

              {/* Pagination */}
              <div className="flex flex-col items-center justify-between gap-2 sm:flex-row">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>
                    Page {page} sur {totalPages}
                  </span>
                  <span>({data?.total ?? 0} jeux)</span>
                </div>
                <div className="flex items-center gap-2">
                  <Select value={perPage} onValueChange={handlePerPageChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PER_PAGE_OPTIONS.map((opt) => (
                        <SelectItem key={opt} value={opt}>
                          {opt} / page
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Button
                    variant="outline"
                    size="icon-sm"
                    disabled={page <= 1}
                    onClick={() => handlePageChange(page - 1)}
                  >
                    <ChevronLeft />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon-sm"
                    disabled={page >= totalPages}
                    onClick={() => handlePageChange(page + 1)}
                  >
                    <ChevronRight />
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
