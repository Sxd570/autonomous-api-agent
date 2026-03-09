import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Path
from strands import Agent
from concurrent.futures import ThreadPoolExecutor
from typing import List

from services.agent_base import AgentFactory

SYSTEM_PROMPT = """
    You are an autonomous API agent.
    You receive user queries and API specifications, write Python code to interact with those APIs, execute it, and return clear responses based on the results.
    Always be concise and precise.
"""

app = FastAPI()

executor = ThreadPoolExecutor(max_workers=4)
active_connections: List[WebSocket] = []


class WebSocketCallback:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.response = ""
        self._loop = asyncio.get_running_loop()

    def __call__(self, **kwargs):
        if "data" in kwargs:
            chunk = kwargs["data"]
            self.response += chunk
            asyncio.run_coroutine_threadsafe(
                self._send_chunk_async(chunk),
                self._loop
            )

    async def _send_chunk_async(self, chunk: str):
        try:
            await self.websocket.send_json({
                "type": "chunk",
                "data": chunk
            })
        except Exception as e:
            print(f"Error sending chunk from callback handler: {e}")

    def clear(self):
        self.response = ""


class AgentUseCase:
    def __init__(self, user_id: str, websocket: WebSocket):
        self.user_id = user_id
        self.websocket = websocket
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        factory = AgentFactory(
            system_prompt=SYSTEM_PROMPT,
            callback_handler=WebSocketCallback(self.websocket, "araa")
        )
        return factory.create_agent()

    async def execute(self, query: str):
        try:
            await self.websocket.send_json({"type": "response_start", "data": ""})

            loop = asyncio.get_running_loop()
            agent_error = None

            def run_agent():
                nonlocal agent_error
                try:
                    self.agent(query)
                except Exception as e:
                    agent_error = e
                    print(f"Agent error for user {self.user_id}: {str(e)}")

            await loop.run_in_executor(executor, run_agent)

            if agent_error:
                await self.websocket.send_json({"type": "response_error", "data": str(agent_error)})

            await self.websocket.send_json({"type": "response_end", "data": ""})

        except WebSocketDisconnect:
            print(f"Client disconnected during execution: {self.user_id}")
        except Exception as e:
            print(f"Error for user {self.user_id}: {str(e)}")
            raise e


@app.websocket("/ws/chat")
async def chat(
    websocket: WebSocket,
    user_id: str = Path(..., description="The ID of the user")
):
    try:
        await websocket.accept()
        active_connections.append(websocket)

        agent_use_case = AgentUseCase(user_id=user_id, websocket=websocket)

        while True:
            message = await websocket.receive_text()
            message = message.strip()

            if not message:
                continue

            await agent_use_case.execute(query=message)

    except WebSocketDisconnect:
        print(f"Client disconnected: {user_id}")
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {str(e)}")
        raise e
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9001, reload=True)