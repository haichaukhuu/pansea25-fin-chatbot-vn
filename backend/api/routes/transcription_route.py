"""
FastAPI routes for transcription service
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
import json
import logging
import base64
import asyncio
from typing import Optional

from core.services.transcription_service import transcription_service
from core.models.transcription_models import TranscriptionRequest, TranscriptionResponse, TranscriptionConfirmation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transcription", tags=["transcription"])


@router.get("/health")
async def transcription_health():
    """Health check for transcription service"""
    try:
        is_initialized = await transcription_service.initialize()
        return {
            "status": "healthy" if is_initialized else "unhealthy",
            "service": "Amazon Transcribe",
            "region": transcription_service.region
        }
    except Exception as e:
        logger.error(f"Transcription health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@router.websocket("/stream")
async def transcription_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription streaming"""
    await websocket.accept()
    session_id = None
    
    try:
        # Wait for initial configuration
        config_data = await websocket.receive_text()
        config = json.loads(config_data)
        
        # Extract transcription parameters - default to Vietnamese 
        language_code = config.get('language_code', 'vi-VN')
        sample_rate = config.get('sample_rate', 16000)
        enable_partial_results = config.get('enable_partial_results', True)
        
        logger.info(f"Starting transcription session with config: {config}")
        
        # Clean up any existing sessions for this connection first
        await transcription_service.cleanup_all_sessions()
        
        # Start transcription session
        session_id, result_generator = await transcription_service.start_transcription_session(
            language_code=language_code,
            sample_rate=sample_rate,
            enable_partial_results=enable_partial_results
        )
        
        logger.info(f"Created new transcription session: {session_id}")
        
        # Send session started confirmation
        await websocket.send_text(json.dumps({
            "type": "session_started",
            "session_id": session_id,
            "status": "ready"
        }))
               
        async def handle_incoming_audio():
            """Handle incoming audio chunks from WebSocket"""
            try:
                while True:
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    if data.get('type') == 'audio_chunk':
                        # Decode base64 audio data
                        audio_data = base64.b64decode(data['audio_data'])
                        await transcription_service.send_audio_chunk(session_id, audio_data)
                        
                    elif data.get('type') == 'end_session':
                        logger.info(f"Received end session request for {session_id}")
                        
                        # Give AWS Transcribe time to send final results before ending
                        await asyncio.sleep(1)

                        await transcription_service.end_transcription_session(session_id)
                        
                        # Additional delay after ending session for cleanup
                        await asyncio.sleep(1)

                        # Send final session ended message to frontend
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "session_ended",
                                "session_id": session_id,
                                "status": "completed"
                            }))
                        except:
                            logger.debug("Could not send session_ended message - websocket already closed")
                        
                        # Gracefully close the websocket to signal normal closure (1000)
                        try:
                            await websocket.close(code=1000)
                        except Exception as close_err:
                            logger.debug(f"WebSocket close during end_session encountered: {close_err}")
                        break
                        
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected during audio handling for session {session_id}")
            except Exception as e:
                logger.error(f"Error handling incoming audio: {e}")
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
                except:
                    logger.warning("Could not send error message to disconnected client")
        
        async def handle_outgoing_results():
            """Handle outgoing transcription results"""
            try:
                async for result in result_generator:
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "transcription_result",
                            "status": result.status.value,
                            "result": result.result.dict() if result.result else None,
                            "error_message": result.error_message,
                            "session_id": result.session_id
                        }))
                    except WebSocketDisconnect:
                        logger.info(f"WebSocket disconnected during result sending for session {session_id}")
                        break
                    except Exception as send_error:
                        logger.warning(f"Error sending result: {send_error}")
                        break
                    
            except Exception as e:
                logger.error(f"Error handling outgoing results: {e}")
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
                except:
                    logger.warning("Could not send error message to disconnected client")
        
        # Run both tasks concurrently
        try:
            await asyncio.gather(
                handle_incoming_audio(),
                handle_outgoing_results(),
                return_exceptions=True
            )
        except Exception as gather_error:
            logger.error(f"Error in websocket task gathering: {gather_error}")
        finally:
            # Add delay before cleanup to let AWS finish processing
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except:
            logger.warning("Could not send error message to disconnected client")
    finally:
        # Only clean up if session still exists to prevent double cleanup
        if session_id and session_id in transcription_service.active_sessions:
            logger.info(f"Cleaning up session {session_id} in finally block")
            await transcription_service.end_transcription_session(session_id)
        elif session_id:
            logger.info(f"Session {session_id} already cleaned up, skipping")
        else:
            # Clean up any orphaned sessions only if no specific session
            logger.info("No session ID, checking for orphaned sessions")
            await transcription_service.cleanup_all_sessions()


@router.post("/confirm")
async def confirm_transcription(confirmation: TranscriptionConfirmation):
    """Confirm and optionally edit transcribed text"""
    try:
        # Return the confirmed text
        final_text = confirmation.edited_transcript or confirmation.original_transcript
        
        return {
            "status": "confirmed",
            "final_text": final_text,
            "was_edited": bool(confirmation.edited_transcript)
        }
        
    except Exception as e:
        logger.error(f"Error confirming transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages for transcription"""
    # Languages supported by Amazon Transcribe with focus on English and Vietnamese
    supported_languages = [
        {"code": "en-US", "name": "English (US)", "country": "US"},
        {"code": "vi-VN", "name": "Vietnamese", "country": "VN"},
        {"code": "en-GB", "name": "English (UK)", "country": "GB"},
        {"code": "es-ES", "name": "Spanish (Spain)", "country": "ES"},
        {"code": "es-US", "name": "Spanish (US)", "country": "US"},
        {"code": "fr-FR", "name": "French", "country": "FR"},
        {"code": "de-DE", "name": "German", "country": "DE"},
        {"code": "it-IT", "name": "Italian", "country": "IT"},
        {"code": "pt-BR", "name": "Portuguese (Brazil)", "country": "BR"},
        {"code": "ja-JP", "name": "Japanese", "country": "JP"},
        {"code": "ko-KR", "name": "Korean", "country": "KR"},
        {"code": "zh-CN", "name": "Chinese (Mandarin)", "country": "CN"}
    ]
    
    return {"languages": supported_languages}
