from pydantic import BaseModel
from typing import Optional
from crewai.flow.flow import Flow, listen, start


class TestState(BaseModel):
    topic_title: str
    topic_description: str
    sentence_count: int = 3
    message: str = ""
    user_id: str | None = None


class TestFlow(Flow[TestState]):
    def __init__(self, state: TestState | None = None):
        """Initialize the test flow with an optional state."""
        if state is not None:
            self.initial_state = state
        super().__init__()

    @start()
    def initialize(self):
        print(f"Starting test flow for user {self.state.user_id}")
        print(f"Topic: {self.state.topic_title}")
        print(f"Description: {self.state.topic_description}")
        print(f"Sentence count: {self.state.sentence_count}")
        self.state.message = "Hello from test flow!"

    @listen(initialize)
    def say_goodbye(self):
        print("Saying goodbye...")
        self.state.message += "\nGoodbye!"
