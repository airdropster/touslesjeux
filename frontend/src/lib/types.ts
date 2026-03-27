export interface Game {
  id: number;
  title: string;
  year: number | null;
  designer: string | null;
  editeur: string | null;
  player_count_min: number | null;
  player_count_max: number | null;
  duration_min: number | null;
  duration_max: number | null;
  age_minimum: number | null;
  complexity_score: number | null;
  summary: string | null;
  regles_detaillees: string | null;
  theme: string[];
  mechanics: string[];
  core_mechanics: string[];
  components: string[];
  type_jeu_famille: string[];
  public: string[];
  niveau_interaction: string | null;
  famille_materiel: string[];
  tags: string[];
  lien_bgg: string | null;
  source_url: string | null;
  status: "enriched" | "skipped" | "failed";
  skip_reason: string | null;
  job_id: number | null;
  scraped_at: string | null;
  enriched_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface Job {
  id: number;
  categories: string[];
  target_count: number;
  processed_count: number;
  skipped_count: number;
  failed_count: number;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface GameStats {
  total: number;
  enriched: number;
  skipped: number;
  failed: number;
}
