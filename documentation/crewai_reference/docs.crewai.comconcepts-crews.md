# Source: https://docs.crewai.com/concepts/crews

## URL: https://docs.crewai.com/concepts/crews

Title: Crews - CrewAI

URL Source: https://docs.crewai.com/concepts/crews

Markdown Content:
What is a Crew?
---------------

A crew in crewAI represents a collaborative group of agents working together to achieve a set of tasks. Each crew defines the strategy for task execution, agent collaboration, and the overall workflow.

Crew Attributes
---------------

| Attribute | Parameters | Description |
| --- | --- | --- |
| **Tasks** | `tasks` | A list of tasks assigned to the crew. |
| **Agents** | `agents` | A list of agents that are part of the crew. |
| **Process** _(optional)_ | `process` | The process flow (e.g., sequential, hierarchical) the crew follows. Default is `sequential`. |
| **Verbose** _(optional)_ | `verbose` | The verbosity level for logging during execution. Defaults to `False`. |
| **Manager LLM** _(optional)_ | `manager_llm` | The language model used by the manager agent in a hierarchical process. **Required when using a hierarchical process.** |
| **Function Calling LLM** _(optional)_ | `function_calling_llm` | If passed, the crew will use this LLM to do function calling for tools for all agents in the crew. Each agent can have its own LLM, which overrides the crew’s LLM for function calling. |
| **Config** _(optional)_ | `config` | Optional configuration settings for the crew, in `Json` or `Dict[str, Any]` format. |
| **Max RPM** _(optional)_ | `max_rpm` | Maximum requests per minute the crew adheres to during execution. Defaults to `None`. |
| **Language** _(optional)_ | `language` | Language used for the crew, defaults to English. |
| **Language File** _(optional)_ | `language_file` | Path to the language file to be used for the crew. |
| **Memory** _(optional)_ | `memory` | Utilized for storing execution memories (short-term, long-term, entity memory). |
| **Memory Config** _(optional)_ | `memory_config` | Configuration for the memory provider to be used by the crew. |
| **Cache** _(optional)_ | `cache` | Specifies whether to use a cache for storing the results of tools’ execution. Defaults to `True`. |
| **Embedder** _(optional)_ | `embedder` | Configuration for the embedder to be used by the crew. Mostly used by memory for now. Default is `{"provider": "openai"}`. |
| **Full Output** _(optional)_ | `full_output` | Whether the crew should return the full output with all tasks outputs or just the final output. Defaults to `False`. |
| **Step Callback** _(optional)_ | `step_callback` | A function that is called after each step of every agent. This can be used to log the agent’s actions or to perform other operations; it won’t override the agent-specific `step_callback`. |
| **Task Callback** _(optional)_ | `task_callback` | A function that is called after the completion of each task. Useful for monitoring or additional operations post-task execution. |
| **Share Crew** _(optional)_ | `share_crew` | Whether you want to share the complete crew information and execution with the crewAI team to make the library better, and allow us to train models. |
| **Output Log File** _(optional)_ | `output_log_file` | Whether you want to have a file with the complete crew output and execution. You can set it using True and it will default to the folder you are currently in and it will be called logs.txt or passing a string with the full path and name of the file. |
| **Manager Agent** _(optional)_ | `manager_agent` | `manager` sets a custom agent that will be used as a manager. |
| **Prompt File** _(optional)_ | `prompt_file` | Path to the prompt JSON file to be used for the crew. |
| **Planning** _(optional)_ | `planning` | Adds planning ability to the Crew. When activated before each Crew iteration, all Crew data is sent to an AgentPlanner that will plan the tasks and this plan will be added to each task description. |
| **Planning LLM** _(optional)_ | `planning_llm` | The language model used by the AgentPlanner in a planning process. |

Creating Crews
--------------

There are two ways to create crews in CrewAI: using **YAML configuration (recommended)** or defining them **directly in code**.

### YAML Configuration (Recommended)

Using YAML configuration provides a cleaner, more maintainable way to define crews and is consistent with how agents and tasks are defined in CrewAI projects.

After creating your CrewAI project as outlined in the [Installation](https://docs.crewai.com/installation) section, you can define your crew in a class that inherits from `CrewBase` and uses decorators to define agents, tasks, and the crew itself.

#### Example Crew Class with Decorators

The `CrewBase` class, along with these decorators, automates the collection of agents and tasks, reducing the need for manual management.

#### Decorators overview from `annotations.py`

CrewAI provides several decorators in the `annotations.py` file that are used to mark methods within your crew class for special handling:

*   `@CrewBase`: Marks the class as a crew base class.
*   `@agent`: Denotes a method that returns an `Agent` object.
*   `@task`: Denotes a method that returns a `Task` object.
*   `@crew`: Denotes the method that returns the `Crew` object.
*   `@before_kickoff`: (Optional) Marks a method to be executed before the crew starts.
*   `@after_kickoff`: (Optional) Marks a method to be executed after the crew finishes.

These decorators help in organizing your crew’s structure and automatically collecting agents and tasks without manually listing them.

### Direct Code Definition (Alternative)

Alternatively, you can define the crew directly in code without using YAML configuration files.

In this example:

*   Agents and tasks are defined directly within the class without decorators.
*   We manually create and manage the list of agents and tasks.
*   This approach provides more control but can be less maintainable for larger projects.

Crew Output
-----------

The output of a crew in the CrewAI framework is encapsulated within the `CrewOutput` class. This class provides a structured way to access results of the crew’s execution, including various formats such as raw strings, JSON, and Pydantic models. The `CrewOutput` includes the results from the final task output, token usage, and individual task outputs.

### Crew Output Attributes

| Attribute | Parameters | Type | Description |
| --- | --- | --- | --- |
| **Raw** | `raw` | `str` | The raw output of the crew. This is the default format for the output. |
| **Pydantic** | `pydantic` | `Optional[BaseModel]` | A Pydantic model object representing the structured output of the crew. |
| **JSON Dict** | `json_dict` | `Optional[Dict[str, Any]]` | A dictionary representing the JSON output of the crew. |
| **Tasks Output** | `tasks_output` | `List[TaskOutput]` | A list of `TaskOutput` objects, each representing the output of a task in the crew. |
| **Token Usage** | `token_usage` | `Dict[str, Any]` | A summary of token usage, providing insights into the language model’s performance during execution. |

### Crew Output Methods and Properties

| Method/Property | Description |
| --- | --- |
| **json** | Returns the JSON string representation of the crew output if the output format is JSON. |
| **to\_dict** | Converts the JSON and Pydantic outputs to a dictionary. |
| \***\*str\*\*** | Returns the string representation of the crew output, prioritizing Pydantic, then JSON, then raw. |

### Accessing Crew Outputs

Once a crew has been executed, its output can be accessed through the `output` attribute of the `Crew` object. The `CrewOutput` class provides various ways to interact with and present this output.

#### Example

Memory Utilization
------------------

Crews can utilize memory (short-term, long-term, and entity memory) to enhance their execution and learning over time. This feature allows crews to store and recall execution memories, aiding in decision-making and task execution strategies.

Cache Utilization
-----------------

Caches can be employed to store the results of tools’ execution, making the process more efficient by reducing the need to re-execute identical tasks.

Crew Usage Metrics
------------------

After the crew execution, you can access the `usage_metrics` attribute to view the language model (LLM) usage metrics for all tasks executed by the crew. This provides insights into operational efficiency and areas for improvement.

Crew Execution Process
----------------------

*   **Sequential Process**: Tasks are executed one after another, allowing for a linear flow of work.
*   **Hierarchical Process**: A manager agent coordinates the crew, delegating tasks and validating outcomes before proceeding. **Note**: A `manager_llm` or `manager_agent` is required for this process and it’s essential for validating the process flow.

### Kicking Off a Crew

Once your crew is assembled, initiate the workflow with the `kickoff()` method. This starts the execution process according to the defined process flow.

### Different Ways to Kick Off a Crew

Once your crew is assembled, initiate the workflow with the appropriate kickoff method. CrewAI provides several methods for better control over the kickoff process: `kickoff()`, `kickoff_for_each()`, `kickoff_async()`, and `kickoff_for_each_async()`.

*   `kickoff()`: Starts the execution process according to the defined process flow.
*   `kickoff_for_each()`: Executes tasks for each agent individually.
*   `kickoff_async()`: Initiates the workflow asynchronously.
*   `kickoff_for_each_async()`: Executes tasks for each agent individually in an asynchronous manner.

These methods provide flexibility in how you manage and execute tasks within your crew, allowing for both synchronous and asynchronous workflows tailored to your needs.

### Replaying from a Specific Task

You can now replay from a specific task using our CLI command `replay`.

The replay feature in CrewAI allows you to replay from a specific task using the command-line interface (CLI). By running the command `crewai replay -t <task_id>`, you can specify the `task_id` for the replay process.

Kickoffs will now save the latest kickoffs returned task outputs locally for you to be able to replay from.

### Replaying from a Specific Task Using the CLI

To use the replay feature, follow these steps:

1.  Open your terminal or command prompt.
2.  Navigate to the directory where your CrewAI project is located.
3.  Run the following command:

To view the latest kickoff task IDs, use:

Then, to replay from a specific task, use:

These commands let you replay from your latest kickoff tasks, still retaining context from previously executed tasks.

---


# Crawl Statistics

- **Source:** https://docs.crewai.com/concepts/crews
- **Depth:** 1
- **Pages processed:** 1
- **Crawl method:** api
- **Duration:** 2.81 seconds
- **Crawl completed:** 12/29/2024, 4:11:42 PM

