from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import random
import asyncio
from difflib import SequenceMatcher


from agent.utils.upload_script import handle_upload
from agent.utils.load_pdf import Paper
from agent.llm import LLM
from agent.sparse_retriever import sparse_retrieve

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


def find_best_matching_pdf(paper_name: str) -> str | None:
    """Find the most relevant PDF file in FILES_DIR that matches the given paper_name."""
    if not os.path.exists(FILES_DIR):
        return None

    pdf_files = [f for f in os.listdir(FILES_DIR) if f.endswith('.pdf')]
    if not pdf_files:
        return None

    # Try exact match first (without .pdf extension)
    exact_match = f"{paper_name}.pdf"
    if exact_match in pdf_files:
        return os.path.join(FILES_DIR, exact_match)

    # Fuzzy match: find the file whose name (without .pdf) has the highest similarity ratio
    best_match = max(
        pdf_files,
        key=lambda f: SequenceMatcher(None, paper_name, f.replace('.pdf', '')).ratio(),
    )
    ratio = SequenceMatcher(None, paper_name, best_match.replace('.pdf', '')).ratio()

    # Only accept matches with reasonable similarity (threshold 0.3 to be lenient)
    if ratio >= 0.3:
        return os.path.join(FILES_DIR, best_match)

    # If no good match found but files exist, return the best one anyway
    return os.path.join(FILES_DIR, best_match)



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

# Chat API
class ChatRequest(BaseModel):
    message: str
    paper_name: str = "none"


llm_client = LLM()

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Send a message to the LLM with optional paper context."""
    try:
        system_prompt = "You are an academic research assistant. Help users understand research papers."
        if request.paper_name != "none":
            system_prompt += f" The user is currently reading the paper: {request.paper_name}"
            

            path_to_file = find_best_matching_pdf(request.paper_name)
            if path_to_file is None:
                raise HTTPException(status_code=404, detail=f"No PDF files found in {FILES_DIR}")
            

            paper = Paper(path_to_file)
            pages = paper.get_pages()

            chunks = []
            for idx in range(0, len(pages)-2):
                chunk = " ".join(pages[idx:idx+3]) # type: ignore
                chunks.append(chunk)

            query = request.message
            retrieved_doc = sparse_retrieve(chunks, query, top_k=1)
            
            if retrieved_doc:
                system_prompt += f"\n\n--- Retrieved Context ---\n{retrieved_doc}\n--- End of Context ---\nUse the above context to answer accurately."
                print("Retrieved context added to system prompt:{}".format(retrieved_doc))

        response = llm_client.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ])

        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount the 'files' directory to serve the PDFs as static assets
# This makes them accessible at http://localhost:8000/static/filename.pdf
app.mount("/static", StaticFiles(directory=FILES_DIR), name="static")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)