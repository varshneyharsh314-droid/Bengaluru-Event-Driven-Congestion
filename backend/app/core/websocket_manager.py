from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"New operator terminal connected. Active sessions: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"Operator terminal disconnected. Active sessions: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """
        Broadcasts messages to all connected screens.
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Handle disconnected clients that didn't clean up
                print(f"Failed to send WS broadcast: {e}")

ws_manager = ConnectionManager()
