# Source: https://docs.crewai.com/concepts/tools

## URL: https://docs.crewai.com/concepts/tools

Title: Tools - CrewAI

URL Source: https://docs.crewai.com/concepts/tools

Markdown Content:
Introduction
------------

CrewAI tools empower agents with capabilities ranging from web searching and data analysis to collaboration and delegating tasks among coworkers. This documentation outlines how to create, integrate, and leverage these tools within the CrewAI framework, including a new focus on collaboration tools.

A tool in CrewAI is a skill or function that agents can utilize to perform various actions. This includes tools from the [CrewAI Toolkit](https://github.com/joaomdmoura/crewai-tools) and [LangChain Tools](https://python.langchain.com/docs/integrations/tools), enabling everything from simple searches to complex interactions and effective teamwork among agents.

*   **Utility**: Crafted for tasks such as web searching, data analysis, content generation, and agent collaboration.
*   **Integration**: Boosts agent capabilities by seamlessly integrating tools into their workflow.
*   **Customizability**: Provides the flexibility to develop custom tools or utilize existing ones, catering to the specific needs of agents.
*   **Error Handling**: Incorporates robust error handling mechanisms to ensure smooth operation.
*   **Caching Mechanism**: Features intelligent caching to optimize performance and reduce redundant operations.

To enhance your agents’ capabilities with crewAI tools, begin by installing our extra tools package:

Here’s an example demonstrating their use:

*   **Error Handling**: All tools are built with error handling capabilities, allowing agents to gracefully manage exceptions and continue their tasks.
*   **Caching Mechanism**: All tools support caching, enabling agents to efficiently reuse previously obtained results, reducing the load on external resources and speeding up the execution time. You can also define finer control over the caching mechanism using the `cache_function` attribute on the tool.

Here is a list of the available tools and their descriptions:

| Tool | Description |
| --- | --- |
| **BrowserbaseLoadTool** | A tool for interacting with and extracting data from web browsers. |
| **CodeDocsSearchTool** | A RAG tool optimized for searching through code documentation and related technical documents. |
| **CodeInterpreterTool** | A tool for interpreting python code. |
| **ComposioTool** | Enables use of Composio tools. |
| **CSVSearchTool** | A RAG tool designed for searching within CSV files, tailored to handle structured data. |
| **DALL-E Tool** | A tool for generating images using the DALL-E API. |
| **DirectorySearchTool** | A RAG tool for searching within directories, useful for navigating through file systems. |
| **DOCXSearchTool** | A RAG tool aimed at searching within DOCX documents, ideal for processing Word files. |
| **DirectoryReadTool** | Facilitates reading and processing of directory structures and their contents. |
| **EXASearchTool** | A tool designed for performing exhaustive searches across various data sources. |
| **FileReadTool** | Enables reading and extracting data from files, supporting various file formats. |
| **FirecrawlSearchTool** | A tool to search webpages using Firecrawl and return the results. |
| **FirecrawlCrawlWebsiteTool** | A tool for crawling webpages using Firecrawl. |
| **FirecrawlScrapeWebsiteTool** | A tool for scraping webpages URL using Firecrawl and returning its contents. |
| **GithubSearchTool** | A RAG tool for searching within GitHub repositories, useful for code and documentation search. |
| **SerperDevTool** | A specialized tool for development purposes, with specific functionalities under development. |
| **TXTSearchTool** | A RAG tool focused on searching within text (.txt) files, suitable for unstructured data. |
| **JSONSearchTool** | A RAG tool designed for searching within JSON files, catering to structured data handling. |
| **LlamaIndexTool** | Enables the use of LlamaIndex tools. |
| **MDXSearchTool** | A RAG tool tailored for searching within Markdown (MDX) files, useful for documentation. |
| **PDFSearchTool** | A RAG tool aimed at searching within PDF documents, ideal for processing scanned documents. |
| **PGSearchTool** | A RAG tool optimized for searching within PostgreSQL databases, suitable for database queries. |
| **Vision Tool** | A tool for generating images using the DALL-E API. |
| **RagTool** | A general-purpose RAG tool capable of handling various data sources and types. |
| **ScrapeElementFromWebsiteTool** | Enables scraping specific elements from websites, useful for targeted data extraction. |
| **ScrapeWebsiteTool** | Facilitates scraping entire websites, ideal for comprehensive data collection. |
| **WebsiteSearchTool** | A RAG tool for searching website content, optimized for web data extraction. |
| **XMLSearchTool** | A RAG tool designed for searching within XML files, suitable for structured data formats. |
| **YoutubeChannelSearchTool** | A RAG tool for searching within YouTube channels, useful for video content analysis. |
| **YoutubeVideoSearchTool** | A RAG tool aimed at searching within YouTube videos, ideal for video data extraction. |

There are two main ways for one to create a CrewAI tool:

### Subclassing `BaseTool`

### Utilizing the `tool` Decorator

### Structured Tools

The `StructuredTool` class wraps functions as tools, providing flexibility and validation while reducing boilerplate. It supports custom schemas and dynamic logic for seamless integration of complex functionalities.

#### Example:

Using `StructuredTool.from_function`, you can wrap a function that interacts with an external API or system, providing a structured interface. This enables robust validation and consistent execution, making it easier to integrate complex functionalities into your applications as demonstrated in the following example:

### Custom Caching Mechanism

Conclusion
----------

Tools are pivotal in extending the capabilities of CrewAI agents, enabling them to undertake a broad spectrum of tasks and collaborate effectively. When building solutions with CrewAI, leverage both custom and existing tools to empower your agents and enhance the AI ecosystem. Consider utilizing error handling, caching mechanisms, and the flexibility of tool arguments to optimize your agents’ performance and capabilities.

---


# Crawl Statistics

- **Source:** https://docs.crewai.com/concepts/tools
- **Depth:** 1
- **Pages processed:** 1
- **Crawl method:** api
- **Duration:** 2.68 seconds
- **Crawl completed:** 12/29/2024, 4:14:35 PM

