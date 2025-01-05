from pydantic import BaseModel
from typing import Optional
from crewai.flow.flow import Flow, listen, start


class TestState(BaseModel):
    message: str = ""
    user_id: Optional[str] = None


class TestFlow(Flow[TestState]):
    @start()
    def initialize(self):
        print(f"Starting test flow for user {self.state.user_id}")
        self.state.message = "Hello from test flow!"

    @listen(initialize)
    def say_goodbye(self):
        print("Saying goodbye...")
        self.state.message += "\nGoodbye!"
