"""
Folder monitoring service for automatic content processing
"""

import asyncio
import os
import shutil
from pathlib import Path
from typing import Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, DirCreatedEvent
import structlog

from app.core.config import settings
from app.services.content_processor import ContentProcessor
from app.services.ai_enhancer import AIEnhancer
from app.services.publisher import PublisherService

logger = structlog.get_logger()

class FolderEventHandler(FileSystemEventHandler):
    """Handle folder creation events for automatic processing"""
    
    def __init__(self):
        self.content_processor = ContentProcessor()
        self.ai_enhancer = AIEnhancer()
        self.publisher = PublisherService()
        self.processing_folders = set()
    
    def on_created(self, event):
        """Handle new folder creation"""
        if isinstance(event, DirCreatedEvent):
            folder_path = event.src_path
            logger.info("New folder detected", folder_path=folder_path)
            
            # Avoid processing the same folder multiple times
            if folder_path not in self.processing_folders:
                self.processing_folders.add(folder_path)
                asyncio.create_task(self.process_folder(folder_path))
    
    async def process_folder(self, folder_path: str):
        """Process a new folder for content extraction and publishing"""
        try:
            logger.info("Starting folder processing", folder_path=folder_path)
            
            # Wait a bit to ensure all files are copied
            await asyncio.sleep(2)
            
            # Extract content from folder
            content_data = await self.content_processor.extract_folder_content(folder_path)
            
            if not content_data:
                logger.warning("No valid content found in folder", folder_path=folder_path)
                await self.move_to_failed(folder_path, "No valid content found")
                return
            
            # Enhance content with AI
            enhanced_content = await self.ai_enhancer.enhance_content(content_data)
            
            # Publish content if auto-publish is enabled
            if settings.AUTO_PUBLISH_ENABLED:
                publishing_results = await self.publisher.publish_content(enhanced_content)
                
                if any(result.get("success") for result in publishing_results):
                    await self.move_to_published(folder_path)
                    logger.info("Folder processed and published successfully", folder_path=folder_path)
                else:
                    await self.move_to_failed(folder_path, "Publishing failed")
                    logger.error("Publishing failed for folder", folder_path=folder_path)
            else:
                # Just move to published folder without publishing
                await self.move_to_published(folder_path)
                logger.info("Folder processed successfully", folder_path=folder_path)
                
        except Exception as e:
            logger.error("Error processing folder", folder_path=folder_path, error=str(e))
            await self.move_to_failed(folder_path, str(e))
        finally:
            self.processing_folders.discard(folder_path)
    
    async def move_to_published(self, folder_path: str):
        """Move processed folder to published directory"""
        try:
            folder_name = os.path.basename(folder_path)
            published_path = os.path.join(settings.PUBLISHED_FOLDERS_PATH, folder_name)
            
            # Ensure unique name if folder already exists
            counter = 1
            original_published_path = published_path
            while os.path.exists(published_path):
                published_path = f"{original_published_path}_{counter}"
                counter += 1
            
            shutil.move(folder_path, published_path)
            logger.info("Folder moved to published", 
                       original_path=folder_path, 
                       published_path=published_path)
        except Exception as e:
            logger.error("Failed to move folder to published", 
                        folder_path=folder_path, 
                        error=str(e))
    
    async def move_to_failed(self, folder_path: str, error_message: str):
        """Move failed folder to failed directory with error info"""
        try:
            folder_name = os.path.basename(folder_path)
            failed_path = os.path.join(settings.FAILED_FOLDERS_PATH, folder_name)
            
            # Ensure unique name if folder already exists
            counter = 1
            original_failed_path = failed_path
            while os.path.exists(failed_path):
                failed_path = f"{original_failed_path}_{counter}"
                counter += 1
            
            shutil.move(folder_path, failed_path)
            
            # Create error log file
            error_file = os.path.join(failed_path, "error.log")
            with open(error_file, "w") as f:
                f.write(f"Processing failed: {error_message}\n")
                f.write(f"Timestamp: 2025-01-28T10:30:00Z\n")
            
            logger.info("Folder moved to failed", 
                       original_path=folder_path, 
                       failed_path=failed_path,
                       error=error_message)
        except Exception as e:
            logger.error("Failed to move folder to failed directory", 
                        folder_path=folder_path, 
                        error=str(e))

class FolderWatcher:
    """Main folder watching service"""
    
    def __init__(self):
        self.observer = Observer()
        self.event_handler = FolderEventHandler()
        self.is_running = False
    
    def start(self):
        """Start folder monitoring"""
        if self.is_running:
            logger.warning("Folder watcher is already running")
            return
        
        # Ensure monitoring directories exist
        os.makedirs(settings.MONITORED_FOLDERS_PATH, exist_ok=True)
        os.makedirs(settings.PUBLISHED_FOLDERS_PATH, exist_ok=True)
        os.makedirs(settings.FAILED_FOLDERS_PATH, exist_ok=True)
        
        # Start watching
        self.observer.schedule(
            self.event_handler,
            settings.MONITORED_FOLDERS_PATH,
            recursive=False
        )
        
        self.observer.start()
        self.is_running = True
        
        logger.info("Folder watcher started", 
                   monitored_path=settings.MONITORED_FOLDERS_PATH)
    
    def stop(self):
        """Stop folder monitoring"""
        if not self.is_running:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_running = False
        
        logger.info("Folder watcher stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of folder watcher"""
        return {
            "is_running": self.is_running,
            "monitored_path": settings.MONITORED_FOLDERS_PATH,
            "published_path": settings.PUBLISHED_FOLDERS_PATH,
            "failed_path": settings.FAILED_FOLDERS_PATH,
            "processing_folders": len(self.event_handler.processing_folders),
        }

# Global folder watcher instance
folder_watcher = FolderWatcher()