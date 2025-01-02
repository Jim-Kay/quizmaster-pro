export interface BlueprintStatus {
    id: string;
    status: 'draft' | 'generating' | 'completed' | 'error' | 'published' | 'archived';
    title: string;
    description: string;
    terminal_objectives_count: number;
    enabling_objectives_count: number;
}

export interface Blueprint {
    id: string;
    title: string;
    description: string;
    topic_id: string;
    created_by: string;
    terminal_objectives: TerminalObjective[];
    terminal_objectives_count: number;
    enabling_objectives_count: number;
    status: BlueprintStatus['status'];
}

export interface TerminalObjective {
    terminal_objective_id: string;
    number: number;
    description: string;
    cognitive_level: string;
    topic_id: string;
    enabling_objectives: EnablingObjective[];
}

export interface EnablingObjective {
    enabling_objective_id: string;
    number: string;
    description: string;
    cognitive_level: string;
    terminal_objective_id: string;
}
