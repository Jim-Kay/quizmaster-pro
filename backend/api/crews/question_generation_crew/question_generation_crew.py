from crewai import Agent, Crew, Task
from crewai.project.crew_base import CrewBase
from crewai.project.annotations import before_kickoff, after_kickoff, agent, task, crew
from .tools.markdown_reader_tool import MarkdownReaderTool
from crewai_tools import SerperDevTool
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

load_dotenv()

@CrewBase
class QuestionGenerationCrew():
    """Question Generation crew for creating assessment questions"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logfolder = None

    @before_kickoff
    def prepare_inputs(self, inputs):
        """
        Modify or validate inputs before starting the crew.
        """
        self.logger.info(f"Preparing inputs: {inputs}")
        # Use the output_folder from inputs directly
        if 'output_folder' in inputs:
            self.logfolder = inputs['output_folder']
            # Create the output directory if it doesn't exist
            os.makedirs(self.logfolder, exist_ok=True)
            self.logger.debug(f"Created/verified output folder: {self.logfolder}")
            inputs['processed'] = True
            return inputs
        else:
            self.logger.error("output_folder not provided in inputs")
            raise ValueError("output_folder must be provided in inputs")

    @after_kickoff
    def finalize_results(self, output):
        """
        Process the crew's output after it finishes.
        """
        if output and hasattr(output, 'model_dump_json'):
            final_json_output = output.model_dump_json(indent=2)
            # Save the final JSON output to a file in the output folder
            if self.logfolder:
                output_file = os.path.join(self.logfolder, 'final.json')
                self.logger.debug(f"Writing final output to: {output_file}")
                # No need to create directory again since it's done in prepare_inputs
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(final_json_output)
                self.logger.info(f"Final JSON Output saved to '{output_file}'.")
            else:
                self.logger.warning("No output folder specified, skipping file output.")
        else:
            self.logger.warning("No valid output to serialize.")
            if output:
                self.logger.debug(f"Output type: {type(output)}")
                self.logger.debug(f"Output content: {output}")

    @agent
    def question_generator_agent(self) -> Agent:
        search_tool = SerperDevTool()
        return Agent(
            config=self.agents_config['question_generator_agent'],
            tools=[search_tool],
            verbose=True,
            allow_delegation=False,
            llm='gpt-4o'
        )

    @agent
    def subject_matter_qa_agent(self) -> Agent:
        search_tool = SerperDevTool()
        return Agent(
            config=self.agents_config['subject_matter_qa_agent'],
            tools=[search_tool],
            verbose=True,
            allow_delegation=False,
            llm='gpt-4o'
        )

    @agent
    def style_qa_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['style_qa_agent'],
            tools=[MarkdownReaderTool()],
            verbose=True,
            allow_delegation=False,
            llm='gpt-4o'
        )

    @agent
    def manager_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['manager_agent'],
            verbose=True,
            allow_delegation=True,
            llm='gpt-4o'
        )

    @task
    def manage_question_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['manage_question_creation_task'],
            agent=self.manager_agent()
        )

    @crew
    def crew(self) -> Crew:
        agents = [
            self.question_generator_agent(),
            self.subject_matter_qa_agent(),
            self.style_qa_agent(),
            self.manager_agent()
        ]

        tasks = [
            self.manage_question_creation_task()
        ]

        return Crew(
            agents=agents,
            tasks=tasks,
            manager_agent=self.manager_agent(),
            verbose=True,
            planning=True,
            memory=False,
            output_log_file=os.path.join(self.logfolder, 'output.log') if self.logfolder else None
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
