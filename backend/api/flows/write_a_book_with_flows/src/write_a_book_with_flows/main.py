#!/usr/bin/env python
import asyncio
from typing import List

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from write_a_book_with_flows.crews.write_book_chapter_crew.write_book_chapter_crew import (
    WriteBookChapterCrew,
)
from write_a_book_with_flows.types import Chapter, ChapterOutline

from .crews.outline_book_crew.outline_crew import OutlineCrew


class BookState(BaseModel):
    title: str | None = None
    book: List[Chapter] = []
    book_outline: List[ChapterOutline] = []
    topic: str = (
        "Exploring the latest trends in AI across different industries as of September 2024"
    )
    goal: str = """
        The goal of this book is to provide a comprehensive overview of the current state of artificial intelligence in September 2024.
        It will delve into the latest trends impacting various industries, analyze significant advancements,
        and discuss potential future developments. The book aims to inform readers about cutting-edge AI technologies
        and prepare them for upcoming innovations in the field.
    """
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.title is None:
            # Generate title from topic if not provided
            self.title = data.get("topic", "").strip()


class BookFlow(Flow[BookState]):
    """A flow for generating a book with multiple chapters."""
    
    def __init__(self, state: BookState | None = None, initial_state: BookState | None = None):
        """Initialize the book flow with an optional state."""
        if state is not None:
            self.initial_state = state
        elif initial_state is not None:
            self.initial_state = initial_state
        else:
            self.initial_state = BookState()
        super().__init__()

    @start()
    def generate_book_outline(self):
        print("Kickoff the Book Outline Crew".encode('utf-8', errors='ignore').decode('utf-8'))
        output = (
            OutlineCrew()
            .crew()
            .kickoff(inputs={"topic": self.state.topic, "goal": self.state.goal})
        )

        chapters = output["chapters"]
        print("Chapters:", str(chapters).encode('utf-8', errors='ignore').decode('utf-8'))

        self.state.book_outline = chapters
        return chapters

    @listen(generate_book_outline)
    async def write_chapters(self):
        print("Writing Book Chapters".encode('utf-8', errors='ignore').decode('utf-8'))
        tasks = []

        async def write_single_chapter(chapter_outline):
            output = (
                WriteBookChapterCrew()
                .crew()
                .kickoff(
                    inputs={
                        "goal": self.state.goal,
                        "topic": self.state.topic,
                        "chapter_title": chapter_outline.title,
                        "chapter_description": chapter_outline.description,
                        "book_outline": [
                            chapter_outline.model_dump_json()
                            for chapter_outline in self.state.book_outline
                        ],
                    }
                )
            )
            title = output["title"]
            content = output["content"]
            # Ensure proper encoding of title and content
            title = str(title).encode('utf-8', errors='ignore').decode('utf-8')
            content = str(content).encode('utf-8', errors='ignore').decode('utf-8')
            chapter = Chapter(title=title, content=content)
            return chapter

        for chapter_outline in self.state.book_outline:
            print(f"Writing Chapter: {str(chapter_outline.title).encode('utf-8', errors='ignore').decode('utf-8')}")
            print(f"Description: {str(chapter_outline.description).encode('utf-8', errors='ignore').decode('utf-8')}")
            # Schedule each chapter writing task
            task = asyncio.create_task(write_single_chapter(chapter_outline))
            tasks.append(task)

        # Await all chapter writing tasks concurrently
        chapters = await asyncio.gather(*tasks)
        print("Newly generated chapters:", str(chapters).encode('utf-8', errors='ignore').decode('utf-8'))
        self.state.book.extend(chapters)

        print("Book Chapters", str(self.state.book).encode('utf-8', errors='ignore').decode('utf-8'))

    @listen(write_chapters)
    async def join_and_save_chapter(self):
        print("Joining and Saving Book Chapters".encode('utf-8', errors='ignore').decode('utf-8'))
        # Combine all chapters into a single markdown string
        book_content = ""

        for chapter in self.state.book:
            # Add the chapter title as an H1 heading
            book_content += f"# {chapter.title}\n\n"
            # Add the chapter content
            book_content += f"{chapter.content}\n\n"

        # The title of the book from self.state.title
        book_title = self.state.title

        # Create the filename by replacing spaces with underscores and adding .md extension
        filename = f"./{book_title.replace(' ', '_')}.md"

        # Save the combined content into the file
        with open(filename, "w", encoding="utf-8") as file:
            file.write(book_content)

        print(f"Book saved as {filename}".encode('utf-8', errors='ignore').decode('utf-8'))
        return book_content


def kickoff():
    poem_flow = BookFlow()
    poem_flow.kickoff()


def plot():
    poem_flow = BookFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
