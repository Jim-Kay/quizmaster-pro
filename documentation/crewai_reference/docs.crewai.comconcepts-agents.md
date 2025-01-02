# Source: https://docs.crewai.com/concepts/agents

## URL: https://docs.crewai.com/concepts/agents

Title: Agents - CrewAI

URL Source: https://docs.crewai.com/concepts/agents

Markdown Content:
Overview of an Agent
--------------------

In the CrewAI framework, an `Agent` is an autonomous unit that can:

*   Perform specific tasks
*   Make decisions based on its role and goal
*   Use tools to accomplish objectives
*   Communicate and collaborate with other agents
*   Maintain memory of interactions
*   Delegate tasks when allowed

Agent Attributes
----------------

| Attribute | Parameter | Type | Description |
| --- | --- | --- | --- |
| **Role** | `role` | `str` | Defines the agent’s function and expertise within the crew. |
| **Goal** | `goal` | `str` | The individual objective that guides the agent’s decision-making. |
| **Backstory** | `backstory` | `str` | Provides context and personality to the agent, enriching interactions. |
| **LLM** _(optional)_ | `llm` | `Union[str, LLM, Any]` | Language model that powers the agent. Defaults to the model specified in `OPENAI_MODEL_NAME` or “gpt-4”. |
| **Tools** _(optional)_ | `tools` | `List[BaseTool]` | Capabilities or functions available to the agent. Defaults to an empty list. |
| **Function Calling LLM** _(optional)_ | `function_calling_llm` | `Optional[Any]` | Language model for tool calling, overrides crew’s LLM if specified. |
| **Max Iterations** _(optional)_ | `max_iter` | `int` | Maximum iterations before the agent must provide its best answer. Default is 20. |
| **Max RPM** _(optional)_ | `max_rpm` | `Optional[int]` | Maximum requests per minute to avoid rate limits. |
| **Max Execution Time** _(optional)_ | `max_execution_time` | `Optional[int]` | Maximum time (in seconds) for task execution. |
| **Memory** _(optional)_ | `memory` | `bool` | Whether the agent should maintain memory of interactions. Default is True. |
| **Verbose** _(optional)_ | `verbose` | `bool` | Enable detailed execution logs for debugging. Default is False. |
| **Allow Delegation** _(optional)_ | `allow_delegation` | `bool` | Allow the agent to delegate tasks to other agents. Default is False. |
| **Step Callback** _(optional)_ | `step_callback` | `Optional[Any]` | Function called after each agent step, overrides crew callback. |
| **Cache** _(optional)_ | `cache` | `bool` | Enable caching for tool usage. Default is True. |
| **System Template** _(optional)_ | `system_template` | `Optional[str]` | Custom system prompt template for the agent. |
| **Prompt Template** _(optional)_ | `prompt_template` | `Optional[str]` | Custom prompt template for the agent. |
| **Response Template** _(optional)_ | `response_template` | `Optional[str]` | Custom response template for the agent. |
| **Allow Code Execution** _(optional)_ | `allow_code_execution` | `Optional[bool]` | Enable code execution for the agent. Default is False. |
| **Max Retry Limit** _(optional)_ | `max_retry_limit` | `int` | Maximum number of retries when an error occurs. Default is 2. |
| **Respect Context Window** _(optional)_ | `respect_context_window` | `bool` | Keep messages under context window size by summarizing. Default is True. |
| **Code Execution Mode** _(optional)_ | `code_execution_mode` | `Literal["safe", "unsafe"]` | Mode for code execution: ‘safe’ (using Docker) or ‘unsafe’ (direct). Default is ‘safe’. |
| **Embedder Config** _(optional)_ | `embedder_config` | `Optional[Dict[str, Any]]` | Configuration for the embedder used by the agent. |
| **Knowledge Sources** _(optional)_ | `knowledge_sources` | `Optional[List[BaseKnowledgeSource]]` | Knowledge sources available to the agent. |
| **Use System Prompt** _(optional)_ | `use_system_prompt` | `Optional[bool]` | Whether to use system prompt (for o1 model support). Default is True. |

Creating Agents
---------------

There are two ways to create agents in CrewAI: using **YAML configuration (recommended)** or defining them **directly in code**.

### YAML Configuration (Recommended)

Using YAML configuration provides a cleaner, more maintainable way to define agents. We strongly recommend using this approach in your CrewAI projects.

After creating your CrewAI project as outlined in the [Installation](https://docs.crewai.com/installation) section, navigate to the `src/latest_ai_development/config/agents.yaml` file and modify the template to match your requirements.

Here’s an example of how to configure agents using YAML:

To use this YAML configuration in your code, create a crew class that inherits from `CrewBase`:

### Direct Code Definition

You can create agents directly in code by instantiating the `Agent` class. Here’s a comprehensive example showing all available parameters:

Let’s break down some key parameter combinations for common use cases:

#### Basic Research Agent

#### Code Development Agent

#### Long-Running Analysis Agent

#### Custom Template Agent

### Parameter Details

#### Critical Parameters

*   `role`, `goal`, and `backstory` are required and shape the agent’s behavior
*   `llm` determines the language model used (default: OpenAI’s GPT-4)

#### Memory and Context

*   `memory`: Enable to maintain conversation history
*   `respect_context_window`: Prevents token limit issues
*   `knowledge_sources`: Add domain-specific knowledge bases

#### Execution Control

*   `max_iter`: Maximum attempts before giving best answer
*   `max_execution_time`: Timeout in seconds
*   `max_rpm`: Rate limiting for API calls
*   `max_retry_limit`: Retries on error

#### Code Execution

*   `allow_code_execution`: Must be True to run code
*   `code_execution_mode`:
    *   `"safe"`: Uses Docker (recommended for production)
    *   `"unsafe"`: Direct execution (use only in trusted environments)

#### Templates

*   `system_template`: Defines agent’s core behavior
*   `prompt_template`: Structures input format
*   `response_template`: Formats agent responses

Agents can be equipped with various tools to enhance their capabilities. CrewAI supports tools from:

*   [CrewAI Toolkit](https://github.com/joaomdmoura/crewai-tools)
*   [LangChain Tools](https://python.langchain.com/docs/integrations/tools)

Here’s how to add tools to an agent:

Agent Memory and Context
------------------------

Agents can maintain memory of their interactions and use context from previous tasks. This is particularly useful for complex workflows where information needs to be retained across multiple tasks.

Important Considerations and Best Practices
-------------------------------------------

### Security and Code Execution

*   When using `allow_code_execution`, be cautious with user input and always validate it
*   Use `code_execution_mode: "safe"` (Docker) in production environments
*   Consider setting appropriate `max_execution_time` limits to prevent infinite loops

### Performance Optimization

*   Use `respect_context_window: true` to prevent token limit issues
*   Set appropriate `max_rpm` to avoid rate limiting
*   Enable `cache: true` to improve performance for repetitive tasks
*   Adjust `max_iter` and `max_retry_limit` based on task complexity

### Memory and Context Management

*   Use `memory: true` for tasks requiring historical context
*   Leverage `knowledge_sources` for domain-specific information
*   Configure `embedder_config` when using custom embedding models
*   Use custom templates (`system_template`, `prompt_template`, `response_template`) for fine-grained control over agent behavior

### Agent Collaboration

*   Enable `allow_delegation: true` when agents need to work together
*   Use `step_callback` to monitor and log agent interactions
*   Consider using different LLMs for different purposes:
    *   Main `llm` for complex reasoning
    *   `function_calling_llm` for efficient tool usage

### Model Compatibility

*   Set `use_system_prompt: false` for older models that don’t support system messages
*   Ensure your chosen `llm` supports the features you need (like function calling)

Troubleshooting Common Issues
-----------------------------

1.  **Rate Limiting**: If you’re hitting API rate limits:
    
    *   Implement appropriate `max_rpm`
    *   Use caching for repetitive operations
    *   Consider batching requests
2.  **Context Window Errors**: If you’re exceeding context limits:
    
    *   Enable `respect_context_window`
    *   Use more efficient prompts
    *   Clear agent memory periodically
3.  **Code Execution Issues**: If code execution fails:
    
    *   Verify Docker is installed for safe mode
    *   Check execution permissions
    *   Review code sandbox settings
4.  **Memory Issues**: If agent responses seem inconsistent:
    
    *   Verify memory is enabled
    *   Check knowledge source configuration
    *   Review conversation history management

Remember that agents are most effective when configured according to their specific use case. Take time to understand your requirements and adjust these parameters accordingly.

---


# Crawl Statistics

- **Source:** https://docs.crewai.com/concepts/agents
- **Depth:** 1
- **Pages processed:** 1
- **Crawl method:** api
- **Duration:** 3.56 seconds
- **Crawl completed:** 12/29/2024, 4:11:16 PM

