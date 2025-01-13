import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/dev/ws/test?token=f9b5645d-898b-4d58-b10a-a6b50a9d234b"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to websocket")
            
            # Wait for initial message
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Send a test message
            test_message = {"type": "test", "data": "Hello from test client"}
            await websocket.send(json.dumps(test_message))
            print(f"Sent: {test_message}")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received: {response}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
