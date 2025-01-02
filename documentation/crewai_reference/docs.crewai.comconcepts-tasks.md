# Source: https://docs.crewai.com/concepts/tasks

## URL: https://docs.crewai.com/concepts/tasks

Title: Tasks - CrewAI

URL Source: https://docs.crewai.com/concepts/tasks

Markdown Content:
Overview of a Task
------------------

In the CrewAI framework, a `Task` is a specific assignment completed by an `Agent`.

Tasks provide all necessary details for execution, such as a description, the agent responsible, required tools, and more, facilitating a wide range of action complexities.

Tasks within CrewAI can be collaborative, requiring multiple agents to work together. This is managed through the task properties and orchestrated by the Crew’s process, enhancing teamwork and efficiency.

### Task Execution Flow

Tasks can be executed in two ways:

*   **Sequential**: Tasks are executed in the order they are defined
*   **Hierarchical**: Tasks are assigned to agents based on their roles and expertise

The execution flow is defined when creating the crew:

Task Attributes
---------------

| Attribute | Parameters | Type | Description |
| --- | --- | --- | --- |
| **Description** | `description` | `str` | A clear, concise statement of what the task entails. |
| **Expected Output** | `expected_output` | `str` | A detailed description of what the task’s completion looks like. |
| **Name** _(optional)_ | `name` | `Optional[str]` | A name identifier for the task. |
| **Agent** _(optional)_ | `agent` | `Optional[BaseAgent]` | The agent responsible for executing the task. |
| **Tools** _(optional)_ | `tools` | `List[BaseTool]` | The tools/resources the agent is limited to use for this task. |
| **Context** _(optional)_ | `context` | `Optional[List["Task"]]` | Other tasks whose outputs will be used as context for this task. |
| **Async Execution** _(optional)_ | `async_execution` | `Optional[bool]` | Whether the task should be executed asynchronously. Defaults to False. |
| **Config** _(optional)_ | `config` | `Optional[Dict[str, Any]]` | Task-specific configuration parameters. |
| **Output File** _(optional)_ | `output_file` | `Optional[str]` | File path for storing the task output. |
| **Output JSON** _(optional)_ | `output_json` | `Optional[Type[BaseModel]]` | A Pydantic model to structure the JSON output. |
| **Output Pydantic** _(optional)_ | `output_pydantic` | `Optional[Type[BaseModel]]` | A Pydantic model for task output. |
| **Callback** _(optional)_ | `callback` | `Optional[Any]` | Function/object to be executed after task completion. |

Creating Tasks
--------------

There are two ways to create tasks in CrewAI: using **YAML configuration (recommended)** or defining them **directly in code**.

### YAML Configuration (Recommended)

Using YAML configuration provides a cleaner, more maintainable way to define tasks. We strongly recommend using this approach to define tasks in your CrewAI projects.

After creating your CrewAI project as outlined in the [Installation](https://docs.crewai.com/installation) section, navigate to the `src/latest_ai_development/config/tasks.yaml` file and modify the template to match your specific task requirements.

Here’s an example of how to configure tasks using YAML:

To use this YAML configuration in your code, create a crew class that inherits from `CrewBase`:

### Direct Code Definition (Alternative)

Alternatively, you can define tasks directly in your code without using YAML configuration:

Task Output
-----------

Understanding task outputs is crucial for building effective AI workflows. CrewAI provides a structured way to handle task results through the `TaskOutput` class, which supports multiple output formats and can be easily passed between tasks.

The output of a task in CrewAI framework is encapsulated within the `TaskOutput` class. This class provides a structured way to access results of a task, including various formats such as raw output, JSON, and Pydantic models.

By default, the `TaskOutput` will only include the `raw` output. A `TaskOutput` will only include the `pydantic` or `json_dict` output if the original `Task` object was configured with `output_pydantic` or `output_json`, respectively.

### Task Output Attributes

| Attribute | Parameters | Type | Description |
| --- | --- | --- | --- |
| **Description** | `description` | `str` | Description of the task. |
| **Summary** | `summary` | `Optional[str]` | Summary of the task, auto-generated from the first 10 words of the description. |
| **Raw** | `raw` | `str` | The raw output of the task. This is the default format for the output. |
| **Pydantic** | `pydantic` | `Optional[BaseModel]` | A Pydantic model object representing the structured output of the task. |
| **JSON Dict** | `json_dict` | `Optional[Dict[str, Any]]` | A dictionary representing the JSON output of the task. |
| **Agent** | `agent` | `str` | The agent that executed the task. |
| **Output Format** | `output_format` | `OutputFormat` | The format of the task output, with options including RAW, JSON, and Pydantic. The default is RAW. |

### Task Methods and Properties

| Method/Property | Description |
| --- | --- |
| **json** | Returns the JSON string representation of the task output if the output format is JSON. |
| **to\_dict** | Converts the JSON and Pydantic outputs to a dictionary. |
| **str** | Returns the string representation of the task output, prioritizing Pydantic, then JSON, then raw. |

### Accessing Task Outputs

Once a task has been executed, its output can be accessed through the `output` attribute of the `Task` object. The `TaskOutput` class provides various ways to interact with and present this output.

#### Example

Task Dependencies and Context
-----------------------------

Tasks can depend on the output of other tasks using the `context` attribute. For example:

Getting Structured Consistent Outputs from Tasks
------------------------------------------------

When you need to ensure that a task outputs a structured and consistent format, you can use the `output_pydantic` or `output_json` properties on a task. These properties allow you to define the expected output structure, making it easier to parse and utilize the results in your application.

### Using `output_pydantic`

The `output_pydantic` property allows you to define a Pydantic model that the task output should conform to. This ensures that the output is not only structured but also validated according to the Pydantic model.

Here’s an example demonstrating how to use output\_pydantic:

In this example:

*   A Pydantic model Blog is defined with title and content fields.
*   The task task1 uses the output\_pydantic property to specify that its output should conform to the Blog model.
*   After executing the crew, you can access the structured output in multiple ways as shown.

#### Explanation of Accessing the Output

1.  Dictionary-Style Indexing: You can directly access the fields using result\[“field\_name”\]. This works because the CrewOutput class implements the **getitem** method.
2.  Directly from Pydantic Model: Access the attributes directly from the result.pydantic object.
3.  Using to\_dict() Method: Convert the output to a dictionary and access the fields.
4.  Printing the Entire Object: Simply print the result object to see the structured output.

### Using `output_json`

The `output_json` property allows you to define the expected output in JSON format. This ensures that the task’s output is a valid JSON structure that can be easily parsed and used in your application.

Here’s an example demonstrating how to use `output_json`:

In this example:

*   A Pydantic model Blog is defined with title and content fields, which is used to specify the structure of the JSON output.
*   The task task1 uses the output\_json property to indicate that it expects a JSON output conforming to the Blog model.
*   After executing the crew, you can access the structured JSON output in two ways as shown.

#### Explanation of Accessing the Output

1.  Accessing Properties Using Dictionary-Style Indexing: You can access the fields directly using result\[“field\_name”\]. This is possible because the CrewOutput class implements the **getitem** method, allowing you to treat the output like a dictionary. In this option, we’re retrieving the title and content from the result.
2.  Printing the Entire Blog Object: By printing result, you get the string representation of the CrewOutput object. Since the **str** method is implemented to return the JSON output, this will display the entire output as a formatted string representing the Blog object.

* * *

By using output\_pydantic or output\_json, you ensure that your tasks produce outputs in a consistent and structured format, making it easier to process and utilize the data within your application or across multiple tasks.

Leverage tools from the [CrewAI Toolkit](https://github.com/joaomdmoura/crewai-tools) and [LangChain Tools](https://python.langchain.com/docs/integrations/tools) for enhanced task performance and agent interaction.

This demonstrates how tasks with specific tools can override an agent’s default set for tailored task execution.

Referring to Other Tasks
------------------------

In CrewAI, the output of one task is automatically relayed into the next one, but you can specifically define what tasks’ output, including multiple, should be used as context for another task.

This is useful when you have a task that depends on the output of another task that is not performed immediately after it. This is done through the `context` attribute of the task:

Asynchronous Execution
----------------------

You can define a task to be executed asynchronously. This means that the crew will not wait for it to be completed to continue with the next task. This is useful for tasks that take a long time to be completed, or that are not crucial for the next tasks to be performed.

You can then use the `context` attribute to define in a future task that it should wait for the output of the asynchronous task to be completed.

Callback Mechanism
------------------

The callback function is executed after the task is completed, allowing for actions or notifications to be triggered based on the task’s outcome.

Accessing a Specific Task Output
--------------------------------

Once a crew finishes running, you can access the output of a specific task by using the `output` attribute of the task object:

Specifying tools in a task allows for dynamic adaptation of agent capabilities, emphasizing CrewAI’s flexibility.

Error Handling and Validation Mechanisms
----------------------------------------

While creating and executing tasks, certain validation mechanisms are in place to ensure the robustness and reliability of task attributes. These include but are not limited to:

*   Ensuring only one output type is set per task to maintain clear output expectations.
*   Preventing the manual assignment of the `id` attribute to uphold the integrity of the unique identifier system.

These validations help in maintaining the consistency and reliability of task executions within the crewAI framework.

Creating Directories when Saving Files
--------------------------------------

You can now specify if a task should create directories when saving its output to a file. This is particularly useful for organizing outputs and ensuring that file paths are correctly structured.

Conclusion
----------

Tasks are the driving force behind the actions of agents in CrewAI. By properly defining tasks and their outcomes, you set the stage for your AI agents to work effectively, either independently or as a collaborative unit. Equipping tasks with appropriate tools, understanding the execution process, and following robust validation practices are crucial for maximizing CrewAI’s potential, ensuring agents are effectively prepared for their assignments and that tasks are executed as intended.

---


# Crawl Statistics

- **Source:** https://docs.crewai.com/concepts/tasks
- **Depth:** 1
- **Pages processed:** 1
- **Crawl method:** api
- **Duration:** 11.95 seconds
- **Crawl completed:** 12/29/2024, 4:11:34 PM

