from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from tools.custom_tool import PDFReaderTool
from datetime import datetime
from models import Assessment  # Import the Pydantic model
from crewai.llm import LLM
from dotenv import load_dotenv
import os

load_dotenv()

@CrewBase
class AssessmentFacilitatorCrew():
    """Assessment crew for conducting assessments"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # Generate a timestamp string
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get project root directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    project_root = os.path.dirname(backend_dir)
    logfolder = os.path.join(project_root, 'logs')

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

    # @agent
    # def topic_agent(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['topic_agent'],
    #         verbose=True,
    #         chain_type='conversation'
    #     )

    @agent
    def blueprint_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['blueprint_agent'],
            tools=[PDFReaderTool()],
            verbose=True,
            allow_delegation=False
        )

    @agent
    def question_generator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['question_generator_agent'],
            verbose=True,
            allow_delegation=False
        )

    @agent
    def subject_matter_qa_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['subject_matter_qa_agent'],
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

    # @task
    # def confirm_topic_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['confirm_topic_task'],
    #         agent=self.topic_agent(),
    #         human_input=True
    #     )

    @task
    def design_blueprint_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_blueprint_task'],
            agent=self.blueprint_agent(),
            output_pydantic=Blueprint
        )

    @task
    def manage_question_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['manage_question_creation_task'],
            agent=self.manager_agent(),
            output_pydantic=Assessment
        )

    @task
    def write_blueprint_task(self) -> Task:
        return Task(
            config=self.tasks_config['write_blueprint_task'],
            agent=self.blueprint_agent()
        )

    @task
    def write_questions_task(self) -> Task:
        return Task(
            config=self.tasks_config['write_questions_task'],
            agent=self.question_generator_agent()
        )

    @task
    def create_final_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_final_assessment_task'],
            agent=self.manager_agent()
        )

    @crew
    def crew(self) -> Crew:
        agents = [
            # self.topic_agent(),
            self.blueprint_agent(),
            self.question_generator_agent(),
            self.subject_matter_qa_agent(),
            self.style_qa_agent(),
            self.manager_agent()
        ]

        tasks = [
            # self.confirm_topic_task(),
            self.design_blueprint_task(),
            self.manage_question_creation_task(),
            self.write_blueprint_task(),
            self.write_questions_task(),
            self.create_final_assessment_task()
        ]

        return Crew(
            agents=agents,
            tasks=tasks,
            manager_agent=self.manager_agent(),
            process=Process.sequential,
            planning=True,
            memory=True,
            verbose=True,
            output_log_file=f'{self.logfolder}\\output_{self.timestamp}.log'
        )
