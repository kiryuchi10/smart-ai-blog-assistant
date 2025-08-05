"""
Folder upload and processing endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.services.file_parser import FileParser
from app.services.ai_writer import AIWriter
from app.services.publisher import Publisher
from app.tasks.post_task import process_folder_async

router = APIRouter()

@router.post("/folder")
async def upload_folder(files: List[UploadFile] = File(...)):
    """
    Upload folder contents and trigger processing
    """
    try:
        # Save uploaded files
        file_paths = []
        for file in files:
            # Save file logic here
            file_paths.append(f"blog_content/pending/{file.filename}")
        
        # Trigger async processing
        task = process_folder_async.delay(file_paths)
        
        return {
            "message": "Folder uploaded successfully",
            "task_id": task.id,
            "files_count": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get processing task status
    """
    # Implementation for task status checking
    return {"task_id": task_id, "status": "processing"}

@router.post("/manual-trigger")
async def manual_trigger(folder_path: str):
    """
    Manually trigger processing for a specific folder
    """
    try:
        task = process_folder_async.delay([folder_path])
        return {
            "message": "Processing triggered",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))