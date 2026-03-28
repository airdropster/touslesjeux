import { useState } from "react";
import type { Game } from "@/lib/types";
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

interface GameFormProps {
  game?: Game;
  onSubmit: (data: Record<string, unknown>) => void;
  isLoading: boolean;
  onCancel: () => void;
}

function arrToStr(arr: string[] | undefined): string {
  return arr?.join(", ") ?? "";
}

function strToArr(str: string): string[] {
  return str
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function GameForm({ game, onSubmit, isLoading, onCancel }: GameFormProps) {
  const [title, setTitle] = useState(game?.title ?? "");
  const [year, setYear] = useState(game?.year?.toString() ?? "");
  const [designer, setDesigner] = useState(game?.designer ?? "");
  const [editeur, setEditeur] = useState(game?.editeur ?? "");
  const [playerMin, setPlayerMin] = useState(game?.player_count_min?.toString() ?? "");
  const [playerMax, setPlayerMax] = useState(game?.player_count_max?.toString() ?? "");
  const [durationMin, setDurationMin] = useState(game?.duration_min?.toString() ?? "");
  const [durationMax, setDurationMax] = useState(game?.duration_max?.toString() ?? "");
  const [ageMinimum, setAgeMinimum] = useState(game?.age_minimum?.toString() ?? "");
  const [complexity, setComplexity] = useState(game?.complexity_score?.toString() ?? "");
  const [summary, setSummary] = useState(game?.summary ?? "");
  const [regles, setRegles] = useState(game?.regles_detaillees ?? "");
  const [theme, setTheme] = useState(arrToStr(game?.theme));
  const [mechanics, setMechanics] = useState(arrToStr(game?.mechanics));
  const [coreMechanics, setCoreMechanics] = useState(arrToStr(game?.core_mechanics));
  const [tags, setTags] = useState(arrToStr(game?.tags));
  const [typeJeuFamille, setTypeJeuFamille] = useState(arrToStr(game?.type_jeu_famille));
  const [publicTarget, setPublicTarget] = useState(arrToStr(game?.public));
  const [familleMateriel, setFamilleMateriel] = useState(arrToStr(game?.famille_materiel));
  const [niveauInteraction, setNiveauInteraction] = useState(game?.niveau_interaction ?? "");
  const [lienBgg, setLienBgg] = useState(game?.lien_bgg ?? "");
  const [titleError, setTitleError] = useState("");
  const [complexityError, setComplexityError] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    // Validate
    let hasError = false;

    if (!title.trim()) {
      setTitleError("Le titre est requis");
      hasError = true;
    } else {
      setTitleError("");
    }

    const complexityNum = complexity ? Number(complexity) : null;
    if (complexityNum != null && (complexityNum < 1 || complexityNum > 10)) {
      setComplexityError("La complexite doit etre entre 1 et 10");
      hasError = true;
    } else {
      setComplexityError("");
    }

    if (hasError) return;

    const numOrNull = (v: string) => (v ? Number(v) : null);

    onSubmit({
      title: title.trim(),
      year: numOrNull(year),
      designer: designer.trim() || null,
      editeur: editeur.trim() || null,
      player_count_min: numOrNull(playerMin),
      player_count_max: numOrNull(playerMax),
      duration_min: numOrNull(durationMin),
      duration_max: numOrNull(durationMax),
      age_minimum: numOrNull(ageMinimum),
      complexity_score: complexityNum,
      summary: summary.trim() || null,
      regles_detaillees: regles.trim() || null,
      theme: strToArr(theme),
      mechanics: strToArr(mechanics),
      core_mechanics: strToArr(coreMechanics),
      tags: strToArr(tags),
      type_jeu_famille: strToArr(typeJeuFamille),
      public: strToArr(publicTarget),
      famille_materiel: strToArr(familleMateriel),
      niveau_interaction: niveauInteraction || null,
      lien_bgg: lienBgg.trim() || null,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic info */}
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium">Informations generales</legend>

        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">
            Titre <span className="text-destructive">*</span>
          </label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} />
          {titleError && <p className="text-xs text-destructive">{titleError}</p>}
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Annee</label>
            <Input type="number" value={year} onChange={(e) => setYear(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Designer</label>
            <Input value={designer} onChange={(e) => setDesigner(e.target.value)} />
          </div>
          <div className="space-y-1 col-span-2">
            <label className="text-xs text-muted-foreground">Editeur</label>
            <Input value={editeur} onChange={(e) => setEditeur(e.target.value)} />
          </div>
        </div>
      </fieldset>

      <Separator />

      {/* Numeric stats */}
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium">Statistiques</legend>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Joueurs min</label>
            <Input type="number" min={1} value={playerMin} onChange={(e) => setPlayerMin(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Joueurs max</label>
            <Input type="number" min={1} value={playerMax} onChange={(e) => setPlayerMax(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Duree min</label>
            <Input type="number" min={1} value={durationMin} onChange={(e) => setDurationMin(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Duree max</label>
            <Input type="number" min={1} value={durationMax} onChange={(e) => setDurationMax(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Age minimum</label>
            <Input type="number" min={1} value={ageMinimum} onChange={(e) => setAgeMinimum(e.target.value)} />
          </div>
        </div>

        <div className="space-y-1 max-w-[200px]">
          <label className="text-xs text-muted-foreground">Complexite (1-10)</label>
          <Input
            type="number"
            min={1}
            max={10}
            value={complexity}
            onChange={(e) => setComplexity(e.target.value)}
          />
          {complexityError && <p className="text-xs text-destructive">{complexityError}</p>}
        </div>
      </fieldset>

      <Separator />

      {/* Text fields */}
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium">Textes</legend>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Resume</label>
          <textarea
            className="w-full min-h-[80px] rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Regles detaillees</label>
          <textarea
            className="w-full min-h-[120px] rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30"
            value={regles}
            onChange={(e) => setRegles(e.target.value)}
          />
        </div>
      </fieldset>

      <Separator />

      {/* Array fields */}
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium">Categories (separees par des virgules)</legend>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Theme</label>
            <Input value={theme} onChange={(e) => setTheme(e.target.value)} placeholder="strategie, medieval..." />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Mecaniques</label>
            <Input value={mechanics} onChange={(e) => setMechanics(e.target.value)} placeholder="placement, encheres..." />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Mecaniques principales</label>
            <Input value={coreMechanics} onChange={(e) => setCoreMechanics(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Tags</label>
            <Input value={tags} onChange={(e) => setTags(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Type / Famille de jeu</label>
            <Input value={typeJeuFamille} onChange={(e) => setTypeJeuFamille(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Public</label>
            <Input value={publicTarget} onChange={(e) => setPublicTarget(e.target.value)} placeholder="famille, expert..." />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Famille materiel</label>
            <Input value={familleMateriel} onChange={(e) => setFamilleMateriel(e.target.value)} />
          </div>
        </div>
      </fieldset>

      <Separator />

      {/* Interaction + Link */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Niveau d'interaction</label>
          <Select value={niveauInteraction || "none"} onValueChange={(v: string | null) => setNiveauInteraction(v === "none" || v == null ? "" : v)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Non defini" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Non defini</SelectItem>
              <SelectItem value="nulle">Nulle</SelectItem>
              <SelectItem value="faible">Faible</SelectItem>
              <SelectItem value="moyenne">Moyenne</SelectItem>
              <SelectItem value="forte">Forte</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Lien BGG</label>
          <Input type="url" value={lienBgg} onChange={(e) => setLienBgg(e.target.value)} placeholder="https://boardgamegeek.com/..." />
        </div>
      </div>

      <Separator />

      {/* Buttons */}
      <div className="flex items-center gap-2">
        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Enregistrement..." : "Enregistrer"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Annuler
        </Button>
      </div>
    </form>
  );
}
