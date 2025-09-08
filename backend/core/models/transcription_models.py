from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class TranscriptionStatus(str, Enum):
    """Transcription status enumeration"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLETED = "completed"
    ERROR = "error"


class TranscriptionRequest(BaseModel):
    """Request model for transcription"""
    language_code: Optional[str] = "en-US"
    sample_rate: Optional[int] = 16000
    enable_partial_results: Optional[bool] = True


class TranscriptionChunk(BaseModel):
    """Model for audio chunk data"""
    audio_data: bytes
    chunk_id: Optional[str] = None


class TranscriptionResult(BaseModel):
    """Model for transcription results"""
    transcript: str
    confidence: Optional[float] = None
    is_partial: bool = False
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    alternatives: Optional[List[str]] = []


class TranscriptionResponse(BaseModel):
    """Response model for transcription"""
    status: TranscriptionStatus
    result: Optional[TranscriptionResult] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None


class TranscriptionConfirmation(BaseModel):
    """Model for user confirmation of transcription"""
    original_transcript: str
    edited_transcript: Optional[str] = None
    confirmed: bool = False
