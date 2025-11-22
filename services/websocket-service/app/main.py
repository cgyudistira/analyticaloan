"""
WebSocket Service for Real-Time Updates
Provides live workflow progress updates to clients
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Set
import asyncio
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# =============================================================================
# APP CONFIGURATION
# =============================================================================

app = FastAPI(
    title="AnalyticaLoan WebSocket Service",
    description="Real-time workflow updates via WebSocket",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# CONNECTION MANAGER
# =============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # Map: workflow_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Map: application_id -> Set of WebSocket connections
        self.application_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        workflow_id: str = None,
        application_id: str = None
    ):
        """Accept WebSocket connection and subscribe to updates"""
        await websocket.accept()
        
        if workflow_id:
            if workflow_id not in self.active_connections:
                self.active_connections[workflow_id] = set()
            self.active_connections[workflow_id].add(websocket)
        
        if application_id:
            if application_id not in self.application_connections:
                self.application_connections[application_id] = set()
            self.application_connections[application_id].add(websocket)
    
    def disconnect(
        self,
        websocket: WebSocket,
        workflow_id: str = None,
        application_id: str = None
    ):
        """Remove WebSocket connection"""
        if workflow_id and workflow_id in self.active_connections:
            self.active_connections[workflow_id].discard(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
        
        if application_id and application_id in self.application_connections:
            self.application_connections[application_id].discard(websocket)
            if not self.application_connections[application_id]:
                del self.application_connections[application_id]
    
    async def send_workflow_update(
        self,
        workflow_id: str,
        message: Dict
    ):
        """Send update to all clients subscribed to workflow"""
        if workflow_id in self.active_connections:
            # Add timestamp
            message['timestamp'] = datetime.utcnow().isoformat()
            
            # Send to all connections
            disconnected = set()
            for connection in self.active_connections[workflow_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections[workflow_id].discard(conn)
    
    async def send_application_update(
        self,
        application_id: str,
        message: Dict
    ):
        """Send update to all clients subscribed to application"""
        if application_id in self.application_connections:
            message['timestamp'] = datetime.utcnow().isoformat()
            
            disconnected = set()
            for connection in self.application_connections[application_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            for conn in disconnected:
                self.application_connections[application_id].discard(conn)
    
    async def broadcast(self, message: Dict):
        """Broadcast to all connected clients"""
        message['timestamp'] = datetime.utcnow().isoformat()
        
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)
        for connections in self.application_connections.values():
            all_connections.update(connections)
        
        disconnected = set()
        for connection in all_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)


manager = ConnectionManager()

# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@app.websocket("/ws/workflow/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for workflow progress updates
    
    Client receives real-time updates as workflow progresses through steps
    """
    await manager.connect(websocket, workflow_id=workflow_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "workflow_id": workflow_id,
            "message": "Connected to workflow updates"
        })
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                data = await websocket.receive_text()
                # Echo back (optional)
                await websocket.send_json({
                    "type": "echo",
                    "received": data
                })
            except WebSocketDisconnect:
                break
    
    except Exception as e:
        print(f"WebSocket error for workflow {workflow_id}: {e}")
    
    finally:
        manager.disconnect(websocket, workflow_id=workflow_id)

@app.websocket("/ws/application/{application_id}")
async def application_websocket(websocket: WebSocket, application_id: str):
    """
    WebSocket endpoint for application updates
    
    Client receives updates about:
    - Document uploads
    - Scoring results
    - Decision changes
    - Status changes
    """
    await manager.connect(websocket, application_id=application_id)
    
    try:
        await websocket.send_json({
            "type": "connection_established",
            "application_id": application_id,
            "message": "Connected to application updates"
        })
        
        while True:
            try:
                data = await websocket.receive_text()
                await websocket.send_json({
                    "type": "echo",
                    "received": data
                })
            except WebSocketDisconnect:
                break
    
    except Exception as e:
        print(f"WebSocket error for application {application_id}: {e}")
    
    finally:
        manager.disconnect(websocket, application_id=application_id)

# =============================================================================
# HTTP ENDPOINTS (for triggering updates)
# =============================================================================

@app.get("/")
async def root():
    return {
        "service": "AnalyticaLoan WebSocket Service",
        "version": "1.0.0",
        "status": "running",
        "active_connections": {
            "workflows": len(manager.active_connections),
            "applications": len(manager.application_connections)
        }
    }

@app.post("/trigger/workflow/{workflow_id}")
async def trigger_workflow_update(workflow_id: str, message: Dict):
    """
    Trigger workflow update (called by other services)
    
    Example message:
    {
        "type": "step_completed",
        "step": 3,
        "step_name": "Credit Bureau Fetch",
        "status": "COMPLETED",
        "progress": 37.5
    }
    """
    await manager.send_workflow_update(workflow_id, message)
    return {"status": "sent", "workflow_id": workflow_id}

@app.post("/trigger/application/{application_id}")
async def trigger_application_update(application_id: str, message: Dict):
    """
    Trigger application update (called by other services)
    
    Example message:
    {
        "type": "document_uploaded",
        "document_id": "doc-123",
        "document_type": "INCOME_STATEMENT",
        "status": "UPLOADED"
    }
    """
    await manager.send_application_update(application_id, message)
    return {"status": "sent", "application_id": application_id}

@app.post("/broadcast")
async def broadcast_message(message: Dict):
    """
    Broadcast message to all connected clients
    
    Example message:
    {
        "type": "system_announcement",
        "message": "System maintenance in 30 minutes"
    }
    """
    await manager.broadcast(message)
    return {"status": "broadcasted", "message": message}

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_workflow_subscriptions": len(manager.active_connections),
        "active_application_subscriptions": len(manager.application_connections)
    }

# =============================================================================
# STARTUP/SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    print("WebSocket Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    print("WebSocket Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006, reload=True)
