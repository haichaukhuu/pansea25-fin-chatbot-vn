"""
Amazon Transcribe service for real-time speech-to-text transcription
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional
import os
import json
import uuid
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..models.transcription_models import TranscriptionResult, TranscriptionStatus, TranscriptionResponse

# Import from config
import sys
import os
# Add the backend directory to path to import config
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(backend_dir)
from config import get_aws_transcribe_config

logger = logging.getLogger(__name__)


class TranscribeEventHandler(TranscriptResultStreamHandler):
    """Custom event handler for Amazon Transcribe streaming"""
    
    def __init__(self, output_stream, callback=None):
        super().__init__(output_stream)
        self.callback = callback
        self._shutdown = False
        
    def shutdown(self):
        """Signal the handler to shutdown gracefully"""
        self._shutdown = True
        
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """Handle transcript events from Amazon Transcribe"""
        # Check if handler is being shutdown to prevent processing cancelled futures
        if self._shutdown:
            logger.debug("Event handler is shutting down, skipping transcript event")
            return
            
        try:
            results = transcript_event.transcript.results
            for result in results:
                # Check again in case shutdown happened during processing
                if self._shutdown:
                    logger.debug("Event handler shutdown during processing, stopping")
                    return
                    
                for alt in result.alternatives:
                    # Calculate average confidence from items
                    confidence = None
                    if hasattr(alt, 'items') and alt.items:
                        confidence_scores = [item.confidence for item in alt.items if hasattr(item, 'confidence') and item.confidence is not None]
                        if confidence_scores:
                            confidence = sum(confidence_scores) / len(confidence_scores)
                    
                    transcription_result = TranscriptionResult(
                        transcript=alt.transcript,
                        confidence=confidence,
                        is_partial=result.is_partial,
                        start_time=result.start_time if hasattr(result, 'start_time') else None,
                        end_time=result.end_time if hasattr(result, 'end_time') else None,
                        alternatives=[item.transcript for item in result.alternatives[1:]] if len(result.alternatives) > 1 else []
                    )
                    
                    # Check callback and shutdown state before calling
                    if self.callback and not self._shutdown:
                        try:
                            await self.callback(transcription_result)
                        except asyncio.CancelledError:
                            logger.debug("Callback was cancelled, handler shutting down")
                            self._shutdown = True
                            return
                        except Exception as callback_error:
                            logger.error(f"Error in callback: {callback_error}")
                        
        except asyncio.CancelledError:
            logger.debug("Event handling was cancelled")
            self._shutdown = True
        except Exception as e:
            if not self._shutdown:
                logger.error(f"Error handling transcript event: {e}") 
                if self.callback:
                    try:
                        await self.callback(None, error=str(e))
                    except (asyncio.CancelledError, Exception) as callback_error:
                        logger.debug(f"Could not send error callback: {callback_error}")


class TranscriptionService:
    """Service for managing Amazon Transcribe streaming"""
    
    def __init__(self):
        # Get AWS transcribe configuration
        aws_config = get_aws_transcribe_config()
        self.access_key_id = aws_config["access_key_id"]
        self.secret_access_key = aws_config["secret_access_key"]
        self.region = aws_config["region"]
        self.client = None
        self.active_sessions = {}
        self._shutdown_event = None
        
    def _validate_aws_credentials(self) -> bool:
  
        try:
            if self.access_key_id and self.secret_access_key:
                session = boto3.Session(
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    region_name=self.region
                )
            else:
                # Fall back to default credentials
                session = boto3.Session()
            
            credentials = session.get_credentials()
            if not credentials:
                return False
            
            # Try to access credentials to validate them
            credentials.access_key
            credentials.secret_key
            return True
            
        except (NoCredentialsError, AttributeError) as e:
            logger.error(f"AWS transcribe credentials validation failed: {e}")
            return False
    
    async def initialize(self) -> bool:
        """Initialize the transcription service"""
        try:
            if self.access_key_id and self.secret_access_key:
                # Temporarily set environment variables for this session
                os.environ['AWS_ACCESS_KEY_ID'] = self.access_key_id
                os.environ['AWS_SECRET_ACCESS_KEY'] = self.secret_access_key
                os.environ['AWS_DEFAULT_REGION'] = self.region
                            
            if not self._validate_aws_credentials():
                logger.error("AWS transcribe credentials not found or invalid")
                return False
            
            # Create client with region only - credentials are resolved automatically
            self.client = TranscribeStreamingClient(region=self.region)
           
            if self._shutdown_event is None:
                self._shutdown_event = asyncio.Event()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize transcription service: {e}")
            return False
    
    async def start_transcription_session(
        self, 
        language_code: str = "vi-VN",  # Default to Vietnamese as per spec
        sample_rate: int = 16000,
        enable_partial_results: bool = True
    ) -> tuple[str, AsyncGenerator]:
        """Start a new transcription session"""
        if not self.client:
            await self.initialize()
            
        if not self.client:
            raise Exception("Failed to initialize Transcribe client")
        
        # Clean up any existing sessions first
        if self.active_sessions:
            logger.warning(f"Found {len(self.active_sessions)} existing sessions, cleaning up...")
            await self.cleanup_all_sessions()
        
        session_id = str(uuid.uuid4())
        
        try:            
            # Start transcription stream
            stream = await self.client.start_stream_transcription(
                language_code=language_code,
                media_sample_rate_hz=sample_rate,
                media_encoding="pcm",
                enable_partial_results_stabilization=enable_partial_results,
                partial_results_stability="medium"  # low, medium, high
            )
            
            # Store session
            self.active_sessions[session_id] = {
                'stream': stream,
                'status': TranscriptionStatus.STARTED,
                'created_at': asyncio.get_event_loop().time()
            }
            
            logger.info(f"Started transcription session: {session_id}")
            
            # Create async generator for results
            async def result_generator():
                event_handler_task = None
                handler = None
                
                try:
                    result_queue = asyncio.Queue()
                    
                    async def handle_result(result: TranscriptionResult, error: str = None):
                        # Check if session is still active before processing results
                        if session_id not in self.active_sessions:
                            logger.warning(f"Received result for inactive session {session_id}, ignoring")
                            return
                            
                        if error:
                            response = TranscriptionResponse(
                                status=TranscriptionStatus.ERROR,
                                error_message=error,
                                session_id=session_id
                            )
                        else:
                            status = TranscriptionStatus.PARTIAL if result.is_partial else TranscriptionStatus.COMPLETED
                            response = TranscriptionResponse(
                                status=status,
                                result=result,
                                session_id=session_id
                            )
                        
                        # Use try_put to avoid blocking on cancelled queues
                        try:
                            await result_queue.put(response)
                        except asyncio.CancelledError:
                            logger.debug(f"Result queue put cancelled for session {session_id}")
                    
                    # Set up event handler with shutdown capability
                    handler = TranscribeEventHandler(stream.output_stream, handle_result)
                    
                    # Start handling events in background task
                    event_handler_task = asyncio.create_task(handler.handle_events())
                    
                    try:
                        while session_id in self.active_sessions:  # Check if session still exists
                            # Check for shutdown event
                            if self._shutdown_event and self._shutdown_event.is_set():
                                logger.info(f"Service shutdown requested, stopping result generator for {session_id}")
                                break
                                
                            # Wait for results with timeout to allow checking if handler is done
                            try:
                                response = await asyncio.wait_for(result_queue.get(), timeout=0.1)
                                yield response
                                
                                # If this is an error response, break the loop
                                if response.status == TranscriptionStatus.ERROR:
                                    break
                                    
                            except asyncio.TimeoutError:
                                # Check if the event handler task is done
                                if event_handler_task.done():
                                    # Process any remaining items in queue
                                    while not result_queue.empty():
                                        try:
                                            response = await asyncio.wait_for(result_queue.get(), timeout=0.01)
                                            yield response
                                        except asyncio.TimeoutError:
                                            break
                                    break
                                continue
                                
                    except asyncio.CancelledError:
                        logger.info(f"Result generator cancelled for session {session_id}")
                        return
                    
                except Exception as e:
                    logger.error(f"Error in transcription session {session_id}: {e}")
                    yield TranscriptionResponse(
                        status=TranscriptionStatus.ERROR,
                        error_message=str(e),
                        session_id=session_id
                    )
                finally:                    
                    # Signal handler to shutdown gracefully
                    if handler:
                        handler.shutdown()
                        # Give it a moment to process the shutdown signal
                        await asyncio.sleep(0.1)
                    
                    # Cancel and wait for event handler task
                    if event_handler_task and not event_handler_task.done():
                        event_handler_task.cancel()
                        try:
                            await asyncio.wait_for(event_handler_task, timeout=2.0)
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            logger.debug(f"Event handler task cleanup completed for session {session_id}")
                    
                    # Clean up session
                    if session_id in self.active_sessions:
                        del self.active_sessions[session_id]
            
            return session_id, result_generator()
            
        except Exception as e:
            logger.error(f"Failed to start transcription session: {e}")
            # Clean up on failure
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            raise
    
    async def send_audio_chunk(self, session_id: str, audio_data: bytes):
        """Send audio chunk to transcription session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        stream = session['stream']
        
        try:
            # Check chunk size - AWS Transcribe has limits
            max_chunk_size = 32 * 1024  # 32KB limit per chunk
            if len(audio_data) > max_chunk_size:
                logger.warning(f"Audio chunk size {len(audio_data)} bytes exceeds limit {max_chunk_size}. Splitting chunk.")
                
                # Split large chunks into smaller ones
                for i in range(0, len(audio_data), max_chunk_size):
                    chunk = audio_data[i:i + max_chunk_size]
                    await stream.input_stream.send_audio_event(audio_chunk=chunk)
                    # Small delay between chunks to prevent overwhelming
                    await asyncio.sleep(0.001)
            else:
                await stream.input_stream.send_audio_event(audio_chunk=audio_data)
                
            session['status'] = TranscriptionStatus.IN_PROGRESS
            
        except Exception as e:
            error_msg = str(e)
            if "too big" in error_msg.lower() or "frame size" in error_msg.lower():
                logger.error(f"Audio chunk too large for session {session_id}. Chunk size: {len(audio_data)} bytes. Error: {e}")
                # Try to split the chunk even smaller
                try:
                    small_chunk_size = 8 * 1024  # 8KB chunks
                    for i in range(0, len(audio_data), small_chunk_size):
                        chunk = audio_data[i:i + small_chunk_size]
                        await stream.input_stream.send_audio_event(audio_chunk=chunk)
                        await asyncio.sleep(0.002)
                    session['status'] = TranscriptionStatus.IN_PROGRESS
                    return
                except Exception as retry_error:
                    logger.error(f"Failed to send even smaller chunks: {retry_error}")
            
            logger.error(f"Failed to send audio chunk for session {session_id}: {e}")
            raise
    
    async def end_transcription_session(self, session_id: str):
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found for cleanup")
            return
        
        try:
            session = self.active_sessions[session_id]
            stream = session['stream']
                        
            # Add delay before ending stream to prevent race conditions
            await asyncio.sleep(0.05)  # 50ms delay to let in-flight requests complete
            
            # End the input stream with timeout to prevent hanging
            try:
                await asyncio.wait_for(stream.input_stream.end_stream(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout while ending input stream for session {session_id}")
            except asyncio.CancelledError:
                logger.info(f"Input stream already cancelled for session {session_id}")
            except Exception as stream_error:
                error_msg = str(stream_error).lower()
                if any(keyword in error_msg for keyword in ["invalidstateerror", "cancelled", "future", "closed"]):
                    logger.info(f"Stream already terminated for session {session_id}: {stream_error}")
                else:
                    logger.error(f"Error ending input stream for session {session_id}: {stream_error}")
            
            # Additional delay after ending stream to let AWS cleanup complete
            await asyncio.sleep(1)
            
            # Update status
            session['status'] = TranscriptionStatus.COMPLETED
            
            logger.info(f"Ended transcription session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error ending transcription session {session_id}: {e}")
        finally:
            # Always remove from active sessions, even if there was an error
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Removed session {session_id} from active sessions")
    
    async def cleanup_all_sessions(self):
        """Clean up all active sessions"""
        session_ids = list(self.active_sessions.keys())
        logger.info(f"Cleaning up {len(session_ids)} active sessions")
        
        # Signal shutdown to prevent new operations
        if self._shutdown_event:
            self._shutdown_event.set()
        
        # Give a moment for ongoing operations to see the shutdown signal
        await asyncio.sleep(1)

        # Clean up sessions
        cleanup_tasks = []
        for session_id in session_ids:
            cleanup_tasks.append(self.end_transcription_session(session_id))
        
        if cleanup_tasks:
            # Wait for all cleanup tasks with timeout
            try:
                await asyncio.wait_for(asyncio.gather(*cleanup_tasks, return_exceptions=True), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Cleanup tasks timed out, forcing completion")
        
        # Clear shutdown event for future sessions
        if self._shutdown_event:
            self._shutdown_event.clear()
        logger.info("All sessions cleaned up")


# Global transcription service instance
transcription_service = TranscriptionService()
