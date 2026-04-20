from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import random
import asyncio


from upload_script import handle_upload

app = FastAPI()

# Enable CORS so your frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# The directory where your PDFs are stored
FILES_DIR = "files"

# Ensure the directory exists
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)



@app.get("/api/papers")
async def list_papers():
    """Returns a list of all PDF filenames in the files directory."""
    try:
        files = [f for f in os.listdir(FILES_DIR) if f.endswith('.pdf')]
        return {"papers": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/api/upload")
async def upload_pdf(pdf: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """Upload a PDF file to the files directory."""
    if not pdf.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save the uploaded file
    dest_path = os.path.join(FILES_DIR, pdf.filename)
    content = await pdf.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    # Run handle_upload in a background thread to avoid blocking the event loop
    background_tasks.add_task(handle_upload, dest_path)

    return {"message": f"{pdf.filename} uploaded successfully, processing in background..."}




@app.get("/graph")
async def get_graph():
    # Read knowledge graph data from JSON file
    json_path = os.path.join(os.path.dirname(__file__), "kg", "knowledge_graph.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    PREDEFINED_COLORS = [
        "#4285f4", "#34a853", "#fbbc04", "#ea4335",
        "#9c27b0", "#ff5722", "#795548", "#607d8b",
        "#00bcd4", "#8bc34a", "#ff9800", "#e91e63",
        "#3f51b5", "#009688", "#ffc107", "#673ab7",
    ]

    # Enrich data with label and color fields
    for item in data:
        item["label"] = item["name"]
        if item["type"] == "node":
            item["color"] = random.choice(PREDEFINED_COLORS)

    return data

@app.get("/kg")
async def get_kg_page():
    """Serve the knowledge graph visualization page."""
    return FileResponse(os.path.join(os.path.dirname(__file__), "kg.html"))

# Mount the 'files' directory to serve the PDFs as static assets
# This makes them accessible at http://localhost:8000/static/filename.pdf
app.mount("/static", StaticFiles(directory=FILES_DIR), name="static")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)