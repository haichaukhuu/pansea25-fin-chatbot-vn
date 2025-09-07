import React, { useState, useRef } from 'react';
import { TranscriptionService } from '../../services/transcriptionService';
import type { TranscriptionResult } from '../../services/transcriptionService';
import { TranscriptionConfirmation } from './TranscriptionConfirmation';
import { LiveTranscriptPopup } from './LiveTranscriptPopup';
import { 
  PaperAirplaneIcon,
  PaperClipIcon,
  MicrophoneIcon,
  StopIcon
} from '@heroicons/react/24/outline';
import { useChat } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';

interface MessageInputProps {
  onSendMessage: (message: string) => Promise<void>;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState<TranscriptionResult | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [showLiveTranscript, setShowLiveTranscript] = useState(false);
  const [partialTranscript, setPartialTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [transcriptionConfidence, setTranscriptionConfidence] = useState<number | undefined>(undefined);
  const transcriptionServiceRef = useRef<TranscriptionService | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { uploadFile, isStreaming, stopGeneration } = useChat();
  const { t, language } = useLanguage();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      await onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      Array.from(files).forEach(file => {
        uploadFile(file);
      });
    }
  };

  const handleVoiceInput = () => {
    if (isRecording) {
      transcriptionServiceRef.current?.stopRecording();
      return;
    }

    // State reset before starting new session
    const resetAllState = () => {
      setPartialTranscript('');
      setFinalTranscript('');
      setTranscriptionConfidence(undefined);
      setTranscriptionResult(null);
      setShowConfirmation(false);
      setShowLiveTranscript(false);
      setIsRecording(false);
    };

    resetAllState();

    // Stop and cleanup any existing transcription service
    if (transcriptionServiceRef.current) {
      console.log('Stopping previous transcription service...');
      transcriptionServiceRef.current.stopRecording();
      transcriptionServiceRef.current = null;
    }

    // Wait a moment for cleanup to complete before starting new session
    setTimeout(() => {
      setShowLiveTranscript(true);

      const languageCode = TranscriptionService.getLanguageCode(language);
      
      // Create a completely new transcription service instance
      transcriptionServiceRef.current = new TranscriptionService(
        (result) => {
          console.log('Final transcription result received:', result);
          if (!showConfirmation) {
            setTranscriptionResult(result);
            setFinalTranscript(result.transcript);
            setTranscriptionConfidence(result.confidence);
            setShowConfirmation(true);
            setShowLiveTranscript(false);
            setIsRecording(false);
          } else {
            console.log('Ignoring duplicate final result - confirmation already shown');
          }
        },
        (error) => {
          console.error('Transcription error:', error);
          alert('Transcription error: ' + error);
          setIsRecording(false);
          setShowLiveTranscript(false);
        },
        (status) => {
          console.log('Transcription status:', status);
          setIsRecording(status === 'recording');
          if (status === 'stopped') {
            setShowLiveTranscript(false);
          }
        },
        (partialResult) => {
          console.log('Partial transcription result:', partialResult);
          setPartialTranscript(partialResult.transcript);
          setTranscriptionConfidence(partialResult.confidence);
        }
      );
      
      // Start recording with the appropriate language
      transcriptionServiceRef.current.startRecording({
        language_code: languageCode,
        sample_rate: 16000,
        enable_partial_results: true
      });
    }, 200);
  };

  return (
    <div className="p-4 shadow-lg bg-white">


      <form 
        onSubmit={handleSubmit} 
        className="flex items-center w-full rounded-lg border-2"
        style={{ borderColor: '#21A691', backgroundColor: '#eeeeee' }}
      >
        {/* File upload button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="p-2 flex items-center justify-center transition-colors"
          style={{ color: '#21A691', backgroundColor: '#eeeeee' }}
          onMouseEnter={(e) => { e.currentTarget.style.color = '#87DF2C'; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = '#21A691'; }}
          title="Upload file"
          disabled={disabled || isStreaming}
        >
          <PaperClipIcon className="h-5 w-5" />
        </button>

        {/* Voice input button */}
        <button
          type="button"
          onClick={handleVoiceInput}
          className={`p-2 flex items-center justify-center transition-all duration-200 ${
            isRecording ? 'animate-pulse' : ''
          }`}
          style={{
            color: isRecording ? '#FF0000' : '#21A691',
            backgroundColor: '#eeeeee',
            transform: isRecording ? 'scale(1.1)' : 'scale(1)'
          }}
          onMouseEnter={(e) => {
            if (!isRecording) e.currentTarget.style.color = '#87DF2C';
          }}
          onMouseLeave={(e) => {
            if (!isRecording) e.currentTarget.style.color = '#21A691';
          }}
          title={isRecording ? t('transcription.stop') : 'Voice input'}
          disabled={disabled || isStreaming}
        >
          {isRecording ? <StopIcon className="h-5 w-5" /> : <MicrophoneIcon className="h-5 w-5" />}
        </button>

        {/* Message input */}
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={isStreaming ? t('input.placeholder_generating') : t('input.placeholder_normal')}
          rows={1}
          disabled={disabled || isStreaming}
          className="flex-1 px-4 py-2 focus:outline-none resize-none disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            minHeight: '42px',
            maxHeight: '120px',
            height: 'auto',
            backgroundColor: '#EEEEEE',
            color: '#27403E'
          }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = 'auto';
            target.style.height = Math.min(target.scrollHeight, 120) + 'px';
          }}
        />

        {/* Send/Stop button */}
        <button
          type={isStreaming ? "button" : "submit"}
          onClick={isStreaming ? stopGeneration : undefined}
          disabled={!isStreaming && (!message.trim() || disabled)}
          className="p-3 flex items-center justify-center rounded-r-lg focus:outline-none disabled:opacity-50 transition-colors font-medium"
          style={{
            backgroundColor: isStreaming ? '#ff4444' : '#87DF2C',
            color: isStreaming ? '#FFFFFF' : '#27403E'
          }}
          onMouseEnter={(e) => {
            if (!e.currentTarget.disabled) {
              e.currentTarget.style.backgroundColor = isStreaming ? '#cc3333' : '#7BC628';
            }
          }}
          onMouseLeave={(e) => {
            if (!e.currentTarget.disabled) {
              e.currentTarget.style.backgroundColor = isStreaming ? '#ff4444' : '#87DF2C';
            }
          }}
          title={isStreaming ? t('input.stop_generation') : t('input.send_message')}
        >
          {isStreaming ? <StopIcon className="h-5 w-5" /> : <PaperAirplaneIcon className="h-5 w-5" />}
        </button>
      </form>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleFileUpload}
        accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.xls,image/*"
      />

      {/* Live Transcript Popup */}
      <LiveTranscriptPopup
        isVisible={showLiveTranscript}
        isRecording={isRecording}
        partialTranscript={partialTranscript}
        finalTranscript={finalTranscript}
        confidence={transcriptionConfidence}
        onStop={() => {
          transcriptionServiceRef.current?.stopRecording();
        }}
        onClose={() => {
          setShowLiveTranscript(false);
          if (isRecording) {
            transcriptionServiceRef.current?.stopRecording();
          }
        }}
      />

      {/* Transcription confirmation dialog */}
      <TranscriptionConfirmation
        transcript={transcriptionResult?.transcript || ''}
        confidence={transcriptionResult?.confidence}
        isVisible={showConfirmation}
        onConfirm={(finalText) => {
          setMessage(finalText);
          setShowConfirmation(false);
          setTranscriptionResult(null);
          setPartialTranscript('');
          setFinalTranscript('');
          setTranscriptionConfidence(undefined);
        }}
        onCancel={() => {
          setShowConfirmation(false);
          setTranscriptionResult(null);
          setPartialTranscript('');
          setFinalTranscript('');
          setTranscriptionConfidence(undefined);
        }}
      />
    </div>
  );
};
