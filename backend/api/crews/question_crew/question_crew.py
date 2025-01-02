from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from tools.custom_tool import PDFReaderTool
from crewai_tools import SerperDevTool
from datetime import datetime
from models import Assessment  # Import the Pydantic model
from crewai.llm import LLM
from dotenv import load_dotenv
import os

load_dotenv()

@CrewBase
class QuestionCrew():
    """Question crew for generating questions"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # Generate a timestamp string
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logfolder = 'C:\\data\\crewai-quizmaster-pro\\logs'

    @before_kickoff
    def prepare_inputs(self, inputs):
        """
        Modify or validate inputs before starting the crew.
        """
        print(f"Preparing inputs: {inputs}")
        # Create a unique folder for this execution under the log folder
        topic_folder = os.path.join(self.logfolder, inputs['topic'].replace(" ", "_"))
        os.makedirs(topic_folder, exist_ok=True)
        inputs['output_folder'] = topic_folder
        inputs['processed'] = True
        return inputs

    @after_kickoff
    def finalize_results(self, output):
        """
        Process the crew's output after it finishes.
        """
        if output and output.pydantic:
            final_json_output = output.pydantic.model_dump_json(indent=2)
            topic_folder = output.pydantic.output_folder
            # Save the final JSON output to a file
            with open(os.path.join(topic_folder, 'final.json'), 'w', encoding='utf-8') as f:
                f.write(final_json_output)
            print("Final JSON Output saved to 'final.json'.")
        else:
            print("No valid output to serialize.")

    @agent
    def question_generator_agent(self) -> Agent:
        search_tool = SerperDevTool()
        return Agent(
            config=self.agents_config['question_generator_agent'],
            tools=[search_tool],
            verbose=True,
            allow_delegation=False
        )

    @agent
    def subject_matter_qa_agent(self) -> Agent:
        search_tool = SerperDevTool()
        return Agent(
            config=self.agents_config['subject_matter_qa_agent'],
            tools=[search_tool],
            verbose=True,
            allow_delegation=False
        )

    @agent
    def style_qa_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['style_qa_agent'],
            tools=[PDFReaderTool()],
            verbose=True,
            allow_delegation=False
        )

    @agent
    def manager_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['manager_agent'],
            verbose=True,
            allow_delegation=True
        )

    @task
    def manage_question_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['manage_question_creation_task'],
            agent=self.manager_agent(),
            output_pydantic=Assessment
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CrewaiResearcher crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            manager_agent=self.manager_agent(),
            verbose=True,
            planning=True,
            memory=True,
            output_log_file=f'{self.logfolder}\\output_{self.timestamp}.log'
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)

    # @crew
    # def crew(self) -> Crew:
    #     agents = [
    #         self.question_generator_agent(),
    #         self.subject_matter_qa_agent(),
    #         self.style_qa_agent(),
    #         self.manager_agent()
    #     ]

    #     tasks = [
    #         self.manage_question_creation_task()
    #     ]

    #     return Crew(
    #         agents=agents,
    #         tasks=tasks,
    #         manager_agent=self.manager_agent(),
    #         process=Process.sequential,
    #         planning=True,
    #         memory=True,
    #         verbose=True,
    #         output_log_file=f'{self.logfolder}\\output_{self.timestamp}.log'
    #     )

