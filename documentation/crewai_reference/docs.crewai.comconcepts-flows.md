# Source: https://docs.crewai.com/concepts/flows

## URL: https://docs.crewai.com/concepts/flows

Title: Flows - CrewAI

URL Source: https://docs.crewai.com/concepts/flows

Markdown Content:
Introduction
------------

CrewAI Flows is a powerful feature designed to streamline the creation and management of AI workflows. Flows allow developers to combine and coordinate coding tasks and Crews efficiently, providing a robust framework for building sophisticated AI automations.

Flows allow you to create structured, event-driven workflows. They provide a seamless way to connect multiple tasks, manage state, and control the flow of execution in your AI applications. With Flows, you can easily design and implement multi-step processes that leverage the full potential of CrewAI’s capabilities.

1.  **Simplified Workflow Creation**: Easily chain together multiple Crews and tasks to create complex AI workflows.
    
2.  **State Management**: Flows make it super easy to manage and share state between different tasks in your workflow.
    
3.  **Event-Driven Architecture**: Built on an event-driven model, allowing for dynamic and responsive workflows.
    
4.  **Flexible Control Flow**: Implement conditional logic, loops, and branching within your workflows.
    

Getting Started
---------------

Let’s create a simple Flow where you will use OpenAI to generate a random city in one task and then use that city to generate a fun fact in another task.

In the above example, we have created a simple Flow that generates a random city using OpenAI and then generates a fun fact about that city. The Flow consists of two tasks: `generate_city` and `generate_fun_fact`. The `generate_city` task is the starting point of the Flow, and the `generate_fun_fact` task listens for the output of the `generate_city` task.

When you run the Flow, it will generate a random city and then generate a fun fact about that city. The output will be printed to the console.

**Note:** Ensure you have set up your `.env` file to store your `OPENAI_API_KEY`. This key is necessary for authenticating requests to the OpenAI API.

### @start()

The `@start()` decorator is used to mark a method as the starting point of a Flow. When a Flow is started, all the methods decorated with `@start()` are executed in parallel. You can have multiple start methods in a Flow, and they will all be executed when the Flow is started.

### @listen()

The `@listen()` decorator is used to mark a method as a listener for the output of another task in the Flow. The method decorated with `@listen()` will be executed when the specified task emits an output. The method can access the output of the task it is listening to as an argument.

#### Usage

The `@listen()` decorator can be used in several ways:

1.  **Listening to a Method by Name**: You can pass the name of the method you want to listen to as a string. When that method completes, the listener method will be triggered.
    
2.  **Listening to a Method Directly**: You can pass the method itself. When that method completes, the listener method will be triggered.
    

### Flow Output

Accessing and handling the output of a Flow is essential for integrating your AI workflows into larger applications or systems. CrewAI Flows provide straightforward mechanisms to retrieve the final output, access intermediate results, and manage the overall state of your Flow.

#### Retrieving the Final Output

When you run a Flow, the final output is determined by the last method that completes. The `kickoff()` method returns the output of this final method.

Here’s how you can access the final output:

In this example, the `second_method` is the last method to complete, so its output will be the final output of the Flow. The `kickoff()` method will return the final output, which is then printed to the console.

#### Accessing and Updating State

In addition to retrieving the final output, you can also access and update the state within your Flow. The state can be used to store and share data between different methods in the Flow. After the Flow has run, you can access the state to retrieve any information that was added or updated during the execution.

Here’s an example of how to update and access the state:

In this example, the state is updated by both `first_method` and `second_method`. After the Flow has run, you can access the final state to see the updates made by these methods.

By ensuring that the final method’s output is returned and providing access to the state, CrewAI Flows make it easy to integrate the results of your AI workflows into larger applications or systems, while also maintaining and accessing the state throughout the Flow’s execution.

Flow State Management
---------------------

Managing state effectively is crucial for building reliable and maintainable AI workflows. CrewAI Flows provides robust mechanisms for both unstructured and structured state management, allowing developers to choose the approach that best fits their application’s needs.

### Unstructured State Management

In unstructured state management, all state is stored in the `state` attribute of the `Flow` class. This approach offers flexibility, enabling developers to add or modify state attributes on the fly without defining a strict schema.

**Key Points:**

*   **Flexibility:** You can dynamically add attributes to `self.state` without predefined constraints.
*   **Simplicity:** Ideal for straightforward workflows where state structure is minimal or varies significantly.

### Structured State Management

Structured state management leverages predefined schemas to ensure consistency and type safety across the workflow. By using models like Pydantic’s `BaseModel`, developers can define the exact shape of the state, enabling better validation and auto-completion in development environments.

**Key Points:**

*   **Defined Schema:** `ExampleState` clearly outlines the state structure, enhancing code readability and maintainability.
*   **Type Safety:** Leveraging Pydantic ensures that state attributes adhere to the specified types, reducing runtime errors.
*   **Auto-Completion:** IDEs can provide better auto-completion and error checking based on the defined state model.

### Choosing Between Unstructured and Structured State Management

*   **Use Unstructured State Management when:**
    
    *   The workflow’s state is simple or highly dynamic.
    *   Flexibility is prioritized over strict state definitions.
    *   Rapid prototyping is required without the overhead of defining schemas.
*   **Use Structured State Management when:**
    
    *   The workflow requires a well-defined and consistent state structure.
    *   Type safety and validation are important for your application’s reliability.
    *   You want to leverage IDE features like auto-completion and type checking for better developer experience.

By providing both unstructured and structured state management options, CrewAI Flows empowers developers to build AI workflows that are both flexible and robust, catering to a wide range of application requirements.

Flow Control
------------

### Conditional Logic: `or`

The `or_` function in Flows allows you to listen to multiple methods and trigger the listener method when any of the specified methods emit an output.

When you run this Flow, the `logger` method will be triggered by the output of either the `start_method` or the `second_method`. The `or_` function is used to listen to multiple methods and trigger the listener method when any of the specified methods emit an output.

### Conditional Logic: `and`

The `and_` function in Flows allows you to listen to multiple methods and trigger the listener method only when all the specified methods emit an output.

When you run this Flow, the `logger` method will be triggered only when both the `start_method` and the `second_method` emit an output. The `and_` function is used to listen to multiple methods and trigger the listener method only when all the specified methods emit an output.

### Router

The `@router()` decorator in Flows allows you to define conditional routing logic based on the output of a method. You can specify different routes based on the output of the method, allowing you to control the flow of execution dynamically.

In the above example, the `start_method` generates a random boolean value and sets it in the state. The `second_method` uses the `@router()` decorator to define conditional routing logic based on the value of the boolean. If the boolean is `True`, the method returns `"success"`, and if it is `False`, the method returns `"failed"`. The `third_method` and `fourth_method` listen to the output of the `second_method` and execute based on the returned value.

When you run this Flow, the output will change based on the random boolean value generated by the `start_method`.

Adding Crews to Flows
---------------------

Creating a flow with multiple crews in CrewAI is straightforward.

You can generate a new CrewAI project that includes all the scaffolding needed to create a flow with multiple crews by running the following command:

This command will generate a new CrewAI project with the necessary folder structure. The generated project includes a prebuilt crew called `poem_crew` that is already working. You can use this crew as a template by copying, pasting, and editing it to create other crews.

### Folder Structure

After running the `crewai create flow name_of_flow` command, you will see a folder structure similar to the following:

| Directory/File | Description |
| --- | --- |
| `name_of_flow/` | Root directory for the flow. |
| ├── `crews/` | Contains directories for specific crews. |
| │ └── `poem_crew/` | Directory for the “poem\_crew” with its configurations and scripts. |
| │ ├── `config/` | Configuration files directory for the “poem\_crew”. |
| │ │ ├── `agents.yaml` | YAML file defining the agents for “poem\_crew”. |
| │ │ └── `tasks.yaml` | YAML file defining the tasks for “poem\_crew”. |
| │ ├── `poem_crew.py` | Script for “poem\_crew” functionality. |
| ├── `tools/` | Directory for additional tools used in the flow. |
| │ └── `custom_tool.py` | Custom tool implementation. |
| ├── `main.py` | Main script for running the flow. |
| ├── `README.md` | Project description and instructions. |
| ├── `pyproject.toml` | Configuration file for project dependencies and settings. |
| └── `.gitignore` | Specifies files and directories to ignore in version control. |

### Building Your Crews

In the `crews` folder, you can define multiple crews. Each crew will have its own folder containing configuration files and the crew definition file. For example, the `poem_crew` folder contains:

*   `config/agents.yaml`: Defines the agents for the crew.
*   `config/tasks.yaml`: Defines the tasks for the crew.
*   `poem_crew.py`: Contains the crew definition, including agents, tasks, and the crew itself.

You can copy, paste, and edit the `poem_crew` to create other crews.

### Connecting Crews in `main.py`

The `main.py` file is where you create your flow and connect the crews together. You can define your flow by using the `Flow` class and the decorators `@start` and `@listen` to specify the flow of execution.

Here’s an example of how you can connect the `poem_crew` in the `main.py` file:

In this example, the `PoemFlow` class defines a flow that generates a sentence count, uses the `PoemCrew` to generate a poem, and then saves the poem to a file. The flow is kicked off by calling the `kickoff()` method.

### Running the Flow

(Optional) Before running the flow, you can install the dependencies by running:

Once all of the dependencies are installed, you need to activate the virtual environment by running:

After activating the virtual environment, you can run the flow by executing one of the following commands:

or

The flow will execute, and you should see the output in the console.

Plot Flows
----------

Visualizing your AI workflows can provide valuable insights into the structure and execution paths of your flows. CrewAI offers a powerful visualization tool that allows you to generate interactive plots of your flows, making it easier to understand and optimize your AI workflows.

### What are Plots?

Plots in CrewAI are graphical representations of your AI workflows. They display the various tasks, their connections, and the flow of data between them. This visualization helps in understanding the sequence of operations, identifying bottlenecks, and ensuring that the workflow logic aligns with your expectations.

### How to Generate a Plot

CrewAI provides two convenient methods to generate plots of your flows:

#### Option 1: Using the `plot()` Method

If you are working directly with a flow instance, you can generate a plot by calling the `plot()` method on your flow object. This method will create an HTML file containing the interactive plot of your flow.

This will generate a file named `my_flow_plot.html` in your current directory. You can open this file in a web browser to view the interactive plot.

#### Option 2: Using the Command Line

If you are working within a structured CrewAI project, you can generate a plot using the command line. This is particularly useful for larger projects where you want to visualize the entire flow setup.

This command will generate an HTML file with the plot of your flow, similar to the `plot()` method. The file will be saved in your project directory, and you can open it in a web browser to explore the flow.

### Understanding the Plot

The generated plot will display nodes representing the tasks in your flow, with directed edges indicating the flow of execution. The plot is interactive, allowing you to zoom in and out, and hover over nodes to see additional details.

By visualizing your flows, you can gain a clearer understanding of the workflow’s structure, making it easier to debug, optimize, and communicate your AI processes to others.

### Conclusion

Plotting your flows is a powerful feature of CrewAI that enhances your ability to design and manage complex AI workflows. Whether you choose to use the `plot()` method or the command line, generating plots will provide you with a visual representation of your workflows, aiding in both development and presentation.

Next Steps
----------

If you’re interested in exploring additional examples of flows, we have a variety of recommendations in our examples repository. Here are four specific flow examples, each showcasing unique use cases to help you match your current problem type to a specific example:

1.  **Email Auto Responder Flow**: This example demonstrates an infinite loop where a background job continually runs to automate email responses. It’s a great use case for tasks that need to be performed repeatedly without manual intervention. [View Example](https://github.com/crewAIInc/crewAI-examples/tree/main/email_auto_responder_flow)
    
2.  **Lead Score Flow**: This flow showcases adding human-in-the-loop feedback and handling different conditional branches using the router. It’s an excellent example of how to incorporate dynamic decision-making and human oversight into your workflows. [View Example](https://github.com/crewAIInc/crewAI-examples/tree/main/lead-score-flow)
    
3.  **Write a Book Flow**: This example excels at chaining multiple crews together, where the output of one crew is used by another. Specifically, one crew outlines an entire book, and another crew generates chapters based on the outline. Eventually, everything is connected to produce a complete book. This flow is perfect for complex, multi-step processes that require coordination between different tasks. [View Example](https://github.com/crewAIInc/crewAI-examples/tree/main/write_a_book_with_flows)
    
4.  **Meeting Assistant Flow**: This flow demonstrates how to broadcast one event to trigger multiple follow-up actions. For instance, after a meeting is completed, the flow can update a Trello board, send a Slack message, and save the results. It’s a great example of handling multiple outcomes from a single event, making it ideal for comprehensive task management and notification systems. [View Example](https://github.com/crewAIInc/crewAI-examples/tree/main/meeting_assistant_flow)
    

By exploring these examples, you can gain insights into how to leverage CrewAI Flows for various use cases, from automating repetitive tasks to managing complex, multi-step processes with dynamic decision-making and human feedback.

Also, check out our YouTube video on how to use flows in CrewAI below!

---


# Crawl Statistics

- **Source:** https://docs.crewai.com/concepts/flows
- **Depth:** 1
- **Pages processed:** 1
- **Crawl method:** api
- **Duration:** 2.60 seconds
- **Crawl completed:** 12/29/2024, 4:12:06 PM

