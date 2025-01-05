import os
import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class PoemCrew:
    """Poem Crew"""

    def __init__(self, state=None):
        self.state = state
        # Get absolute paths to config files
        config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
        
        # Load agent config
        with open(os.path.join(config_dir, "agents.yaml"), 'r') as f:
            self.agents_config = yaml.safe_load(f)
            
        # Load task config
        with open(os.path.join(config_dir, "tasks.yaml"), 'r') as f:
            self.tasks_config = yaml.safe_load(f)
            
        super().__init__()

    @agent
    def poem_writer(self) -> Agent:
        """Create the poem writer agent."""
        config = self.agents_config["poem_writer"].copy()
        # Enable verbose mode to see agent's thought process
        config["verbose"] = True
        return Agent(**config)

    @task
    def write_poem(self) -> Task:
        """Create the poem writing task."""
        config = self.tasks_config["write_poem"].copy()
        # Format the description with the current state
        config["description"] = config["description"].format(state=self.state)
        # Enable verbose mode to see task execution details
        config["verbose"] = True
        return Task(**config)

    @crew
    def crew(self) -> Crew:
        """Creates the Poem Crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,  # Enable verbose mode for the crew
        )
