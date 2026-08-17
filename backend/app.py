import asyncio
import json
import os
import sys
import shutil
import uuid
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from engine.orchestrator import ResearchOrchestrator
from agents.profiler import DataProfilerAgent

app = FastAPI(title="Autonomous AI Scientist API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
UPLOADS_DIR = os.path.join(WORKSPACE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# In-memory session store
sessions: Dict[str, Dict[str, Any]] = {}
event_queues: Dict[str, asyncio.Queue] = {}

class InvestigateRequest(BaseModel):
    csv_filename: str
    domain_context: Optional[str] = ""
    target_column: Optional[str] = None
    task_type: Optional[str] = None

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "system": "Autonomous AI Scientist Engine",
        "active_sessions": len(sessions)
    }

@app.get("/api/sample-datasets")
def list_sample_datasets():
    datasets = []
    if os.path.exists(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            if f.endswith(".csv"):
                fpath = os.path.join(DATA_DIR, f)
                datasets.append({
                    "name": f,
                    "size_bytes": os.path.getsize(fpath),
                    "path": fpath
                })
    return {"samples": datasets}

@app.get("/api/dataset-preview/{filename}")
def get_dataset_preview(filename: str):
    csv_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(csv_path):
        csv_path = os.path.join(UPLOADS_DIR, filename)

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail=f"Dataset file '{filename}' not found.")

    profiler = DataProfilerAgent()
    profile = profiler.profile_csv(csv_path)
    return {"profile": profile}

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    saved_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    saved_path = os.path.join(UPLOADS_DIR, saved_filename)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    profiler = DataProfilerAgent()
    profile = profiler.profile_csv(saved_path)

    return {
        "filename": saved_filename,
        "original_name": file.filename,
        "path": saved_path,
        "size_bytes": os.path.getsize(saved_path),
        "profile": profile
    }

def run_orchestrator_background(
    session_id: str,
    csv_path: str,
    domain_context: str,
    target_column: Optional[str],
    task_type: Optional[str],
    queue: asyncio.Queue,
    loop: asyncio.AbstractEventLoop
):
    orchestrator = ResearchOrchestrator(working_dir=WORKSPACE_DIR)

    def event_cb(event):
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)

    try:
        results = orchestrator.run_investigation(
            csv_path,
            domain_context=domain_context,
            target_override=target_column,
            task_type_override=task_type,
            event_callback=event_cb
        )
        sessions[session_id]["status"] = "completed"
        sessions[session_id]["results"] = results
        asyncio.run_coroutine_threadsafe(queue.put({"stage": "COMPLETE", "agent": "System", "message": "Investigation completed successfully!"}), loop)
    except Exception as e:
        sessions[session_id]["status"] = "failed"
        sessions[session_id]["error"] = str(e)
        asyncio.run_coroutine_threadsafe(queue.put({"stage": "ERROR", "agent": "System", "message": f"Pipeline Error: {str(e)}"}), loop)

@app.post("/api/investigate")
async def start_investigation(req: InvestigateRequest, background_tasks: BackgroundTasks):
    csv_path = os.path.join(DATA_DIR, req.csv_filename)
    if not os.path.exists(csv_path):
        csv_path = os.path.join(UPLOADS_DIR, req.csv_filename)

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail=f"Dataset file '{req.csv_filename}' not found.")

    session_id = uuid.uuid4().hex[:12]
    queue = asyncio.Queue()
    event_queues[session_id] = queue

    sessions[session_id] = {
        "session_id": session_id,
        "status": "running",
        "csv_filename": req.csv_filename,
        "domain_context": req.domain_context,
        "target_column": req.target_column,
        "task_type": req.task_type,
        "created_at": os.path.getmtime(csv_path),
        "results": None
    }

    loop = asyncio.get_event_loop()
    background_tasks.add_task(
        run_orchestrator_background,
        session_id,
        csv_path,
        req.domain_context,
        req.target_column,
        req.task_type,
        queue,
        loop
    )

    return {
        "session_id": session_id,
        "status": "running",
        "message": "Scientific investigation started."
    }

@app.get("/api/stream/{session_id}")
async def stream_logs(session_id: str):
    if session_id not in event_queues:
        raise HTTPException(status_code=404, detail="Session not found")

    queue = event_queues[session_id]

    async def event_generator():
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("stage") in ["COMPLETE", "ERROR"]:
                    break
            except asyncio.TimeoutError:
                yield "data: {\"stage\": \"PING\", \"message\": \"keep-alive\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/results/{session_id}")
def get_results(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.get("/api/download-notebook/{session_id}")
def download_notebook(session_id: str):
    if session_id not in sessions or not sessions[session_id].get("results"):
        raise HTTPException(status_code=404, detail="Results not ready or session not found")
    
    nb_path = sessions[session_id]["results"]["notebook_path"]
    if not os.path.exists(nb_path):
        raise HTTPException(status_code=404, detail="Notebook file missing")

    return FileResponse(nb_path, media_type="application/x-ipynb+json", filename=os.path.basename(nb_path))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5050)





