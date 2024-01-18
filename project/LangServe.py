from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain.prompts import PromptTemplate
from langchain_community.llms import Tongyi
import os
from langserve import add_routes
from langchain.pydantic_v1 import BaseModel
from typing import Any
from fastapi import FastAPI, UploadFile, File
import shutil
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
from FSTools.OcrTool import OcrTool
from FSTools.AsrTool import AsrTool
from FSTools.DocTool import DocTool
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory import (
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
)
from langchain.chains import LLMChain


os.environ["DASHSCOPE_API_KEY"] = ""

llm = Tongyi(model_name="qwen-max-1201")


class Input(BaseModel):
    input: str


class Output(BaseModel):
    output: Any


tools = [
    YahooFinanceNewsTool(),
    OcrTool(),
    AsrTool(),
    DocTool(),
]

prompt = PromptTemplate.from_template(
    """Have a conversation with a human, answer the following questions as best you can. You have access to the following tools:{tools}
Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question
Begin!
{chat_history}
Question: {input}
Thought:{agent_scratchpad}"""
)

agent = create_react_agent(llm, tools, prompt)
finace_agent = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=tools, verbose=True
)


app = FastAPI(
    title="FSAGI Server",
    version="1.0",
    description="A simple api server using Runnable interfaces",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_routes(
    app,
    finace_agent.with_types(input_type=Input, output_type=Output),
    path="/finace",
)


@app.post("/chat")
async def chat(message: dict):
    print("=" * 100)
    print("message", message)
    print("=" * 100)
    session_id = ""

    if message["session_id"] is None:
        session_id = str(uuid.uuid4())
    else:
        session_id = message["session_id"]

    message_history = RedisChatMessageHistory(
        session_id, ttl=86400, url="redis://127.0.0.1:6379"
    )
    memory = ConversationBufferWindowMemory(
        k=10, memory_key="chat_history", chat_memory=message_history
    )
    # memory = ConversationSummaryBufferMemory(
    #     llm=llm,
    #     max_token_limit=1,
    #     return_messages=True,
    #     chat_memory=message_history,
    #     memory_key="chat_history",
    # )
    agent_chain = AgentExecutor.from_agent_and_tools(
        agent=agent, tools=tools, verbose=True, memory=memory
    )

    response = agent_chain.invoke({"input": message["input"]})

    result = {"output": response, "session_id": session_id}

    print("=" * 100)
    print("result", result)
    print("=" * 100)

    return result


@app.post("/uploadfile")
async def create_upload_file(file: UploadFile = File(...)):
    print("=" * 100)
    print(file.filename)
    print("=" * 100)
    random_uuid = str(uuid.uuid4())
    path = os.path.join(os.getcwd(), "uploaded_files")
    filename_list = file.filename.split(".")
    new_name = ""

    if len(filename_list) > 1:
        suffix = filename_list[-1]
        new_name = ".".join([random_uuid, suffix])
    else:
        new_name = random_uuid
    new_name = file.filename

    if not os.path.exists(path):
        os.makedirs(path)

    whole_path = os.path.join(path, new_name)
    try:
        with open(f"{whole_path}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    return [{"filename": new_name}]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="192.168.66.12", port=8000)
