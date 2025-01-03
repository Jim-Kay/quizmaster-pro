import json
import logging
from pathlib import Path
from typing import Dict, Any, Union
from datetime import datetime
import os
import uuid
import yaml
from crewai import Agent, Task, Crew, Process
from api.schemas.pydantic_schemas import BlueprintPydantic
from api.schemas.enums import CognitiveLevelEnum

logger = logging.getLogger(__name__)

class BlueprintCrew:
    """Blueprint crew for generating objective blueprints"""

    def __init__(self, inputs: Dict[str, Any] = None):
        """Initialize the blueprint crew with optional inputs."""
        self.inputs = inputs
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get project root directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        project_root = os.path.dirname(backend_dir)
        self.logfolder = os.path.join(project_root, 'logs')
        os.makedirs(self.logfolder, exist_ok=True)
        
        # Load YAML configurations
        config_dir = os.path.join(os.path.dirname(__file__), 'config')
        with open(os.path.join(config_dir, 'agents.yaml'), 'r') as f:
            self.agents_config = yaml.safe_load(f)
        with open(os.path.join(config_dir, 'tasks.yaml'), 'r') as f:
            self.tasks_config = yaml.safe_load(f)

    def prepare_inputs(self, inputs: Dict[str, Any]):
        """Prepare the inputs for the crew."""
        self.inputs = inputs

    def _normalize_cognitive_level(self, level: str) -> str:
        """Normalize cognitive level to match database enum.
        
        Args:
            level: The cognitive level string to normalize
            
        Returns:
            str: The normalized cognitive level string that matches the database enum
        """
        if not level:
            return None
            
        # Convert to uppercase and try to match with enum
        level_upper = level.upper()
        try:
            # Return the value directly as a string since it's already uppercase
            if level_upper in ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"]:
                return level_upper
            else:
                logger.error(f"Invalid cognitive level: {level}")
                # Default to "REMEMBER" if invalid
                return "REMEMBER"
        except ValueError:
            logger.error(f"Invalid cognitive level: {level}")
            # Default to "REMEMBER" if invalid
            return "REMEMBER"

    def _extract_blueprint_from_result(self, result) -> BlueprintPydantic:
        """Extract the Blueprint model from the result.
        
        Args:
            result: The final output from the crew's execution
            
        Returns:
            BlueprintPydantic: The extracted blueprint model
            
        Raises:
            ValueError: If the blueprint data is empty or invalid
        """
        try:
            # If result is already a BlueprintPydantic instance, return it
            if isinstance(result, BlueprintPydantic):
                return result
                
            # Get the Blueprint model from the last task
            if hasattr(result, 'tasks_output') and result.tasks_output:
                last_task_output = result.tasks_output[-1]
                if hasattr(last_task_output, 'pydantic') and last_task_output.pydantic:
                    return last_task_output.pydantic
                elif hasattr(last_task_output, 'raw'):
                    result = last_task_output.raw
            
            # If result is a string, try to parse it as JSON
            if isinstance(result, str):
                try:
                    blueprint_data = json.loads(result)
                except json.JSONDecodeError:
                    # If the string is not valid JSON, try to extract JSON from it
                    import re
                    json_pattern = r'\{[^{}]*\}'
                    matches = re.findall(json_pattern, result)
                    if matches:
                        blueprint_data = json.loads(matches[0])
                    else:
                        raise ValueError("Could not find valid JSON in the result string")
            else:
                blueprint_data = result

            # Normalize cognitive levels and set titles in terminal objectives
            if 'terminal_objectives' in blueprint_data:
                for to in blueprint_data['terminal_objectives']:
                    # Set title from description if not present
                    if 'title' not in to or not to['title']:
                        # Extract first sentence and clean it up
                        description = to.get('description', '')
                        first_sentence = description.split('.')[0].strip()
                        # Make sure the title meets minimum length requirement
                        if len(first_sentence) < 3:
                            first_sentence = description[:50] + '...'  # Use first 50 chars if sentence is too short
                        to['title'] = first_sentence
                    
                    to['cognitive_level'] = self._normalize_cognitive_level(to['cognitive_level'])
                    
                    if 'enabling_objectives' in to:
                        for eo in to['enabling_objectives']:
                            # Set title from description if not present
                            if 'title' not in eo or not eo['title']:
                                # Extract first sentence and clean it up
                                description = eo.get('description', '')
                                first_sentence = description.split('.')[0].strip()
                                # Make sure the title meets minimum length requirement
                                if len(first_sentence) < 3:
                                    first_sentence = description[:50] + '...'  # Use first 50 chars if sentence is too short
                                eo['title'] = first_sentence
                                
                            eo['cognitive_level'] = self._normalize_cognitive_level(eo['cognitive_level'])

            # Create a BlueprintPydantic instance
            blueprint = BlueprintPydantic(**blueprint_data)
            return blueprint

        except Exception as e:
            logger.error(f"Error extracting blueprint from result: {str(e)}")
            logger.error(f"Raw result: {result}")
            if hasattr(result, '__dict__'):
                logger.error(f"Result attributes: {result.__dict__}")
            raise ValueError(f"Failed to extract blueprint from result: {str(e)}")

    def _update_blueprint_metadata(self, blueprint: BlueprintPydantic) -> None:
        """Update the blueprint's metadata with input values.
        
        Args:
            blueprint: The blueprint to update
        """
        blueprint.blueprint_id = self.inputs.get('blueprint_id')
        blueprint.topic_id = self.inputs.get('topic_id')
        blueprint.created_by = self.inputs.get('created_by', '550e8400-e29b-41d4-a716-446655440000')  # Default UUID
        blueprint.output_folder = self.inputs.get('output_folder')

    def _generate_objective_ids(self, blueprint: BlueprintPydantic) -> None:
        """Generate UUIDs for terminal and enabling objectives.
        
        Args:
            blueprint: The blueprint containing objectives to update
        """
        for terminal_obj in blueprint.terminal_objectives:
            terminal_obj.terminal_objective_id = uuid.uuid4()
            terminal_obj.topic_id = blueprint.topic_id

            for enabling_obj in terminal_obj.enabling_objectives:
                enabling_obj.enabling_objective_id = uuid.uuid4()
                enabling_obj.terminal_objective_id = terminal_obj.terminal_objective_id

    def _update_objective_counts(self, blueprint: BlueprintPydantic) -> None:
        """Update the counts of terminal and enabling objectives.
        
        Args:
            blueprint: The blueprint to update counts for
        """
        blueprint.terminal_objectives_count = len(blueprint.terminal_objectives)
        blueprint.enabling_objectives_count = sum(len(to.enabling_objectives) for to in blueprint.terminal_objectives)

    def _save_blueprint_to_file(self, blueprint: BlueprintPydantic) -> None:
        """Save the blueprint to a file if output folder is specified.
        
        Args:
            blueprint: The blueprint to save
        """
        if blueprint.output_folder:
            os.makedirs(blueprint.output_folder, exist_ok=True)
            file_path = os.path.join(blueprint.output_folder, f"blueprint_{blueprint.blueprint_id}.json")
            blueprint.file_path = file_path
            blueprint.save_to_file()
            logger.info(f"Saved blueprint to: {file_path}")

    def finalize_results(self, result) -> BlueprintPydantic:
        """Process the crew's final output and create a Blueprint object.
        
        Args:
            result: The final output from the crew's execution
            
        Returns:
            BlueprintPydantic: A new Blueprint instance with the generated content
            
        Raises:
            ValueError: If the result cannot be parsed into a Blueprint
        """
        try:
            logger.info("Starting finalize_results")
            logger.info(f"Input result type: {type(result)}")
            
            # Extract and validate blueprint
            logger.info("Extracting blueprint from result")
            blueprint = self._extract_blueprint_from_result(result)
            logger.info(f"Extracted blueprint type: {type(blueprint)}")
            
            # Log inputs before update
            logger.info("Current inputs:")
            for key, value in self.inputs.items():
                logger.info(f"  {key}: {value}")
            
            # Log blueprint before update
            logger.info("Current blueprint state:")
            logger.info(f"  blueprint_id: {blueprint.blueprint_id}")
            logger.info(f"  topic_id: {blueprint.topic_id}")
            logger.info(f"  created_by: {blueprint.created_by}")
            
            # Update metadata and generate IDs
            logger.info("Updating blueprint metadata")
            self._update_blueprint_metadata(blueprint)
            
            # Log blueprint after metadata update
            logger.info("Blueprint state after metadata update:")
            logger.info(f"  blueprint_id: {blueprint.blueprint_id}")
            logger.info(f"  topic_id: {blueprint.topic_id}")
            logger.info(f"  created_by: {blueprint.created_by}")
            
            logger.info("Generating objective IDs")
            self._generate_objective_ids(blueprint)
            
            # Update counts and save
            logger.info("Updating objective counts")
            self._update_objective_counts(blueprint)
            
            logger.info("Saving blueprint to file")
            self._save_blueprint_to_file(blueprint)

            logger.info("Successfully finalized blueprint")
            return blueprint

        except Exception as e:
            logger.error(f"Error in finalize_results: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details:", exc_info=True)
            logger.error(f"Raw result: {result}")
            raise

    def blueprint_agent(self) -> Agent:
        """Create and return the blueprint agent."""
        return Agent(
            **{
                **self.agents_config['blueprint_agent'],
                'goal': self.agents_config['blueprint_agent']['goal'].format(
                    topic=self.inputs['topic'],
                    topic_description=self.inputs['description']
                ),
                'backstory': self.agents_config['blueprint_agent']['backstory'].format(
                    topic=self.inputs['topic'],
                    topic_description=self.inputs['description']
                )
            }
        )

    def design_blueprint_task(self) -> Task:
        """Create and return the blueprint design task."""
        return Task(
            **{
                **self.tasks_config['design_blueprint_task'],
                'description': self.tasks_config['design_blueprint_task']['description'].format(
                    topic=self.inputs['topic'],
                    topic_description=self.inputs['description']
                ),
                'expected_output': self.tasks_config['design_blueprint_task']['expected_output'].format(
                    topic=self.inputs['topic'],
                    topic_description=self.inputs['description']
                ),
                'output_pydantic': BlueprintPydantic  # Configure task to return a Pydantic model
            }
        )

    def crew(self) -> Crew:
        """Create and return a crew for blueprint generation."""
        # Create agent and task
        agent = self.blueprint_agent()
        task = self.design_blueprint_task()
        task.agent = agent  # Assign agent to task
        
        # Create log filename using os.path.join for proper path handling
        log_filename = f'output_{self.timestamp}.log'
        output_log_file = os.path.join(self.logfolder, log_filename)

        # Create the crew with our agent and task
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            planning=False,
            memory=False,
            verbose=True,
            output_log_file=output_log_file
        )
        return crew

    def run(self) -> BlueprintPydantic:
        """Run the blueprint generation crew and return the results.
        
        Returns:
            BlueprintPydantic: The generated blueprint
            
        Raises:
            ValueError: If the crew execution fails or results cannot be finalized
        """
        try:
            logger.info("Starting blueprint generation crew")
            crew = self.crew()
            logger.info("Executing crew tasks")
            result = crew.kickoff()
            logger.info("Crew execution completed")
            
            # Process and finalize the results
            logger.info("Processing crew results")
            blueprint = self.finalize_results(result)
            logger.info("Blueprint generation completed successfully")
            
            return blueprint
            
        except Exception as e:
            logger.error(f"Error running blueprint crew: {str(e)}")
            logger.error("Error details:", exc_info=True)
            raise ValueError(f"Blueprint generation failed: {str(e)}")
