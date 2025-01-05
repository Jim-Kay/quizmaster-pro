#!/usr/bin/env python
from random import randint
from typing import TypeVar, Generic

from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start

from .crews.poem_crew.poem_crew import PoemCrew


class PoemState(BaseModel):
    topic_title: str
    topic_description: str
    sentence_count: int = 3
    poem: str = ""
    user_id: str | None = None


class PoemFlow(Flow[PoemState]):
    """A flow for generating poems based on a topic."""
    
    def __init__(self, state: PoemState | None = None):
        """Initialize the poem flow with an optional initial state."""
        if state is not None:
            self.initial_state = state
        super().__init__()

    @start()
    def initialize(self):
        """Start generating the poem."""
        print(f"Starting poem flow for user {self.state.user_id}")
        print(f"Writing a {self.state.sentence_count}-sentence poem about {self.state.topic_title}")
        print(f"Description: {self.state.topic_description}")
        
        crew = PoemCrew(state=self.state)
        result = crew.crew().kickoff()
        self.state.poem = result.tasks_output[0].raw  # Get the raw output from the first task

    @listen(initialize)
    def finalize(self):
        """Finalize the poem generation."""
        print("Poem has been written!")
        print(self.state.poem)


def kickoff():
    poem_flow = PoemFlow()
    poem_flow.kickoff()


def plot():
    poem_flow = PoemFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
