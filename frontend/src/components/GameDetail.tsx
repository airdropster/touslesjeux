import { useState } from "react";
import type { Game } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Users,
  Clock,
  Baby,
  Brain,
} from "lucide-react";

const statusConfig: Record<
  Game["status"],
  { label: string; variant: "default" | "secondary" | "destructive" }
> = {
  enriched: { label: "Enrichi", variant: "default" },
  skipped: { label: "Ignore", variant: "secondary" },
  failed: { label: "Echoue", variant: "destructive" },
};

function formatRange(min: number | null, max: number | null, suffix = "") {
  if (min == null && max == null) return "-";
  if (min != null && max != null && min === max) return `${min}${suffix}`;
  if (min != null && max != null) return `${min} - ${max}${suffix}`;
  if (min != null) return `${min}+${suffix}`;
  return `${max}${suffix}`;
}

function formatDate(iso: string | null) {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("fr-FR", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface GameDetailProps {
  game: Game;
}

export function GameDetail({ game }: GameDetailProps) {
  const [rulesOpen, setRulesOpen] = useState(false);
  const cfg = statusConfig[game.status];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">{game.title}</h2>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          {game.year && <span>{game.year}</span>}
          {game.designer && (
            <>
              <span>&middot;</span>
              <span>{game.designer}</span>
            </>
          )}
          {game.editeur && (
            <>
              <span>&middot;</span>
              <span>{game.editeur}</span>
            </>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card size="sm">
          <CardContent className="flex items-center gap-2">
            <Users className="size-4 text-muted-foreground" />
            <div>
              <div className="text-xs text-muted-foreground">Joueurs</div>
              <div className="font-medium">
                {formatRange(game.player_count_min, game.player_count_max)}
              </div>
            </div>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent className="flex items-center gap-2">
            <Clock className="size-4 text-muted-foreground" />
            <div>
              <div className="text-xs text-muted-foreground">Duree</div>
              <div className="font-medium">
                {formatRange(game.duration_min, game.duration_max, " min")}
              </div>
            </div>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent className="flex items-center gap-2">
            <Baby className="size-4 text-muted-foreground" />
            <div>
              <div className="text-xs text-muted-foreground">Age minimum</div>
              <div className="font-medium">
                {game.age_minimum != null ? `${game.age_minimum}+` : "-"}
              </div>
            </div>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent className="flex items-center gap-2">
            <Brain className="size-4 text-muted-foreground" />
            <div>
              <div className="text-xs text-muted-foreground">Complexite</div>
              <div className="font-medium">
                {game.complexity_score != null ? (
                  <span>
                    {game.complexity_score}
                    <span className="text-muted-foreground">/10</span>
                  </span>
                ) : (
                  "-"
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary */}
      {game.summary && (
        <div>
          <h3 className="mb-1 text-sm font-medium">Resume</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">{game.summary}</p>
        </div>
      )}

      {/* Badges section */}
      <div className="space-y-3">
        <BadgeGroup label="Theme" items={game.theme} />
        <BadgeGroup label="Mecaniques" items={game.mechanics} variant="secondary" />
        <BadgeGroup label="Mecaniques principales" items={game.core_mechanics} variant="default" />
        <BadgeGroup label="Tags" items={game.tags} variant="outline" />
        <BadgeGroup label="Type / Famille" items={game.type_jeu_famille} variant="secondary" />
        <BadgeGroup label="Public" items={game.public} variant="outline" />
        <BadgeGroup label="Materiel" items={game.famille_materiel} variant="outline" />

        {game.niveau_interaction && (
          <div>
            <span className="mr-2 text-xs text-muted-foreground">Interaction:</span>
            <Badge variant="secondary">{game.niveau_interaction}</Badge>
          </div>
        )}
      </div>

      {/* Rules (collapsible) */}
      {game.regles_detaillees && (
        <div>
          <button
            type="button"
            className="flex items-center gap-1 text-sm font-medium hover:text-foreground"
            onClick={() => setRulesOpen((v) => !v)}
          >
            Regles detaillees
            {rulesOpen ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
          </button>
          {rulesOpen && (
            <div className="mt-2 max-h-[500px] overflow-y-auto rounded-lg border bg-muted/30 p-4 text-sm leading-relaxed whitespace-pre-wrap">
              {game.regles_detaillees}
            </div>
          )}
        </div>
      )}

      <Separator />

      {/* External links */}
      <div className="flex flex-wrap gap-2">
        {game.lien_bgg && (
          <Button variant="outline" size="sm" render={<a href={game.lien_bgg} target="_blank" rel="noopener noreferrer" />}>
            <ExternalLink className="mr-1 size-3" />
            BoardGameGeek
          </Button>
        )}
        {game.source_url && (
          <Button variant="outline" size="sm" render={<a href={game.source_url} target="_blank" rel="noopener noreferrer" />}>
            <ExternalLink className="mr-1 size-3" />
            Source
          </Button>
        )}
      </div>

      {/* Status info */}
      <Card size="sm">
        <CardHeader>
          <CardTitle className="text-sm">Informations</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <dt className="text-muted-foreground">Statut</dt>
            <dd><Badge variant={cfg.variant}>{cfg.label}</Badge></dd>

            {game.skip_reason && (
              <>
                <dt className="text-muted-foreground">Raison</dt>
                <dd>{game.skip_reason}</dd>
              </>
            )}

            <dt className="text-muted-foreground">Scraped</dt>
            <dd>{formatDate(game.scraped_at)}</dd>

            <dt className="text-muted-foreground">Enrichi</dt>
            <dd>{formatDate(game.enriched_at)}</dd>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}

function BadgeGroup({
  label,
  items,
  variant = "secondary",
}: {
  label: string;
  items: string[];
  variant?: "default" | "secondary" | "destructive" | "outline";
}) {
  if (items.length === 0) return null;
  return (
    <div>
      <span className="mr-2 text-xs text-muted-foreground">{label}:</span>
      <div className="mt-0.5 inline-flex flex-wrap gap-1">
        {items.map((item) => (
          <Badge key={item} variant={variant}>
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}
