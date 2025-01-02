export interface Blueprint {
  blueprint_id: string;
  title: string;
  description: string;
  topic_id: string;
  created_by: string | null;
  terminal_objectives: TerminalObjective[];
  output_folder: string | null;
  file_path: string | null;
  terminal_objectives_count: number;
  enabling_objectives_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}

interface TerminalObjective {
  terminal_objective_id: string;
  title: string;
  number: number;
  description: string;
  cognitive_level: string;
  topic_id: string | null;
  enabling_objectives: EnablingObjective[];
}

interface EnablingObjective {
  enabling_objective_id: string;
  title: string;
  number: string;
  description: string;
  cognitive_level: string;
  terminal_objective_id: string | null;
}
