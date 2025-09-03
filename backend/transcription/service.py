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

from .models import TranscriptionResult, TranscriptionStatus, TranscriptionResponse

logger = logging.getLogger(__name__)


class TranscribeEventHandler(TranscriptResultStreamHandler):
    """Custom event handler for Amazon Transcribe streaming"""
    
    def __init__(self, output_stream, callback=None):
        super().__init__(output_stream)
        self.callback = callback
        
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """Handle transcript events from Amazon Transcribe"""
        try:
            results = transcript_event.transcript.results
            for result in results:
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
                    
                    if self.callback:
                        await self.callback(transcription_result)
                        
        except Exception as e:
            logger.error(f"Error handling transcript event: {e}") 
            if self.callback:
                await self.callback(None, error=str(e))


class TranscriptionService:
    """Service for managing Amazon Transcribe streaming"""
    
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-west-2')
        self.client = None
        self.active_sessions = {}
        
    def _validate_aws_credentials(self) -> bool:
        """Validate AWS credentials"""
        try:
            # Check if credentials are available
            session = boto3.Session()
            credentials = session.get_credentials()
            if not credentials:
                return False
            
            # Try to access credentials to validate them
            credentials.access_key
            credentials.secret_key
            return True
            
        except (NoCredentialsError, AttributeError) as e:
            logger.error(f"AWS credentials validation failed: {e}")
            return False
    
    async def initialize(self) -> bool:
        """Initialize the transcription service"""
        try:
            if not self._validate_aws_credentials():
                logger.error("AWS credentials not found or invalid")
                return False
                
            self.client = TranscribeStreamingClient(region=self.region)
            logger.info(f"Transcription service initialized for region: {self.region}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize transcription service: {e}")
            return False
    
    async def start_transcription_session(
        self, 
        language_code: str = "en-US",
        sample_rate: int = 16000,
        enable_partial_results: bool = True
    ) -> tuple[str, AsyncGenerator]:
        """Start a new transcription session"""
        if not self.client:
            await self.initialize()
            
        if not self.client:
            raise Exception("Failed to initialize Transcribe client")
        
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
                'status': TranscriptionStatus.STARTED
            }
            
            logger.info(f"Started transcription session: {session_id}")
            
            # Create async generator for results
            async def result_generator():
                try:
                    result_queue = asyncio.Queue()
                    
                    async def handle_result(result: TranscriptionResult, error: str = None):
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
                        await result_queue.put(response)
                    
                    # Set up event handler
                    handler = TranscribeEventHandler(stream.output_stream, handle_result)
                    
                    # Start handling events in background task
                    event_handler_task = asyncio.create_task(handler.handle_events())
                    
                    try:
                        while True:
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
                                        response = await result_queue.get()
                                        yield response
                                    break
                                continue
                                
                    except asyncio.CancelledError:
                        logger.info(f"Result generator cancelled for session {session_id}")
                        event_handler_task.cancel()
                        return
                    finally:
                        # Ensure the event handler task is cancelled
                        if not event_handler_task.done():
                            event_handler_task.cancel()
                            try:
                                await event_handler_task
                            except asyncio.CancelledError:
                                pass
                    
                except Exception as e:
                    logger.error(f"Error in transcription session {session_id}: {e}")
                    yield TranscriptionResponse(
                        status=TranscriptionStatus.ERROR,
                        error_message=str(e),
                        session_id=session_id
                    )
                finally:
                    # Clean up session
                    if session_id in self.active_sessions:
                        del self.active_sessions[session_id]
            
            return session_id, result_generator()
            
        except Exception as e:
            logger.error(f"Failed to start transcription session: {e}")
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
        """End a transcription session"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found for cleanup")
            return
        
        try:
            session = self.active_sessions[session_id]
            stream = session['stream']
            
            # End the input stream
            await stream.input_stream.end_stream()
            
            # Update status
            session['status'] = TranscriptionStatus.COMPLETED
            
            logger.info(f"Ended transcription session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error ending transcription session {session_id}: {e}")
        finally:
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
    
    def get_session_status(self, session_id: str) -> Optional[TranscriptionStatus]:
        """Get status of a transcription session"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]['status']
        return None
    
    async def cleanup_all_sessions(self):
        """Clean up all active sessions"""
        session_ids = list(self.active_sessions.keys())
        for session_id in session_ids:
            await self.end_transcription_session(session_id)


# Global transcription service instance
transcription_service = TranscriptionService()
