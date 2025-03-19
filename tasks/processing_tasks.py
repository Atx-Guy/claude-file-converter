# tasks/processing_tasks.py
import os
import logging
import threading
import queue
import time
from datetime import datetime
from models import db, Conversion
from services.audio_service import AudioService
from services.image_service import ImageService
from services.document_service import DocumentService
from services.pdf_service import PDFService

logger = logging.getLogger(__name__)

# Task processing queue
task_queue = queue.Queue()

# Service instances
audio_service = AudioService()
image_service = ImageService()
document_service = DocumentService()
pdf_service = PDFService()

def process_task_worker():
    """Background worker that processes tasks from the queue."""
    while True:
        try:
            # Get task from queue
            task = task_queue.get()
            
            if task is None:  # Shutdown signal
                break
                
            logger.info(f"Processing task: {task['operation']}")
            
            # Process task based on operation type
            if task['operation'] == 'convert_audio':
                output_path = audio_service.convert_audio(
                    task['input_path'], 
                    task['output_path'],
                    task.get('options', {})
                )
                
            elif task['operation'] == 'convert_image':
                output_path = image_service.convert_image(
                    task['input_path'], 
                    task['output_path'],
                    task.get('options', {})
                )
                
            elif task['operation'] == 'convert_document':
                output_path = document_service.convert_document(
                    task['input_path'], 
                    task['output_path']
                )
                
            elif task['operation'] == 'pdf_split':
                pdf_service.split_pdf(
                    task['input_path'], 
                    task['page_ranges']
                )
                
            elif task['operation'] == 'pdf_merge':
                pdf_service.merge_pdfs(
                    task['input_paths'], 
                    task.get('output_filename')
                )
                
            elif task['operation'] == 'pdf_compress':
                pdf_service.compress_pdf(
                    task['input_path'], 
                    task.get('quality', 'medium')
                )
                
            # Update conversion status if user_id is provided
            if task.get('user_id') and task.get('conversion_id'):
                from app import app
                with app.app_context():
                    conversion = Conversion.query.get(task['conversion_id'])
                    if conversion:
                        conversion.status = 'completed'
                        conversion.completed_at = datetime.utcnow()
                        db.session.commit()
            
            # Execute callback if provided
            if 'callback' in task and callable(task['callback']):
                task['callback'](output_path if 'output_path' in locals() else None)
                
            logger.info(f"Task completed: {task['operation']}")
            
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            
            # Update conversion status to 'failed' if user_id is provided
            if task.get('user_id') and task.get('conversion_id'):
                from app import app
                with app.app_context():
                    conversion = Conversion.query.get(task['conversion_id'])
                    if conversion:
                        conversion.status = 'failed'
                        conversion.error_message = str(e)
                        db.session.commit()
        
        finally:
            # Mark task as done
            task_queue.task_done()

# Start background worker thread
worker_thread = threading.Thread(target=process_task_worker, daemon=True)
worker_thread.start()

def queue_task(task_data):
    """
    Queue a task for background processing.
    
    Args:
        task_data (dict): Task data dictionary
        
    Returns:
        int: Queue size after adding the task
    """
    task_queue.put(task_data)
    return task_queue.qsize()

def shutdown_workers():
    """Shut down worker threads gracefully."""
    task_queue.put(None)  # Signal worker to shut down
    worker_thread.join(timeout=5.0)