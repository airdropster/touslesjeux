import { useState } from "react";
import type { KeyboardEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { X } from "lucide-react";

interface CategorySelectorProps {
  categories: string[];
  onChange: (cats: string[]) => void;
}

export function CategorySelector({ categories, onChange }: CategorySelectorProps) {
  const [input, setInput] = useState("");

  function addCategory(raw: string) {
    const cat = raw.trim().toLowerCase();
    if (cat && !categories.includes(cat)) {
      onChange([...categories, cat]);
    }
    setInput("");
  }

  function removeCategory(cat: string) {
    onChange(categories.filter((c) => c !== cat));
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addCategory(input);
    }
  }

  return (
    <div className="space-y-2">
      <Input
        placeholder="Ajouter une categorie (Entree ou virgule pour valider)"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <Badge key={cat} variant="secondary" className="gap-1">
              {cat}
              <button
                type="button"
                onClick={() => removeCategory(cat)}
                className="ml-0.5 rounded-full hover:bg-muted"
                aria-label={`Supprimer ${cat}`}
              >
                <X className="size-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
