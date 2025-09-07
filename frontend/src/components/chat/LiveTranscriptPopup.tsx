import React, { useEffect, useState } from 'react';
import { 
  MicrophoneIcon,
  StopIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';
import { useLanguage } from '../../context/LanguageContext';

interface LiveTranscriptPopupProps {
  isVisible: boolean;
  isRecording: boolean;
  partialTranscript: string;
  finalTranscript: string;
  onStop: () => void;
  onClose: () => void;
  confidence?: number;
}

export const LiveTranscriptPopup: React.FC<LiveTranscriptPopupProps> = ({
  isVisible,
  isRecording,
  partialTranscript,
  finalTranscript,
  onStop,
  onClose,
  confidence
}) => {
  const { t } = useLanguage();
  const [audioLevel, setAudioLevel] = useState(0);
  
  // Simulate audio level animation for visual feedback
  useEffect(() => {
    if (!isRecording) {
      setAudioLevel(0);
      return;
    }

    const interval = setInterval(() => {
      setAudioLevel(Math.random() * 100);
    }, 100);

    return () => clearInterval(interval);
  }, [isRecording]);

  if (!isVisible) return null;

  const confidenceColor = confidence && confidence > 0.8 
    ? '#22c55e' 
    : confidence && confidence > 0.6 
      ? '#f59e0b' 
      : '#ef4444';

  return (
    <div className="fixed top-4 right-4 z-50 max-w-md w-full mx-4">
      <div 
        className="bg-white rounded-lg shadow-xl border-2 p-4"
        style={{ 
          borderColor: isRecording ? '#FF0000' : '#21A691',
          backgroundColor: '#FFFFFF'
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            {isRecording ? (
              <div className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full animate-pulse"
                  style={{ backgroundColor: '#FF0000' }}
                ></div>
                <span 
                  className="text-sm font-medium"
                  style={{ color: '#FF0000' }}
                >
                  {t('input.recording')}
                </span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <MicrophoneIcon 
                  className="h-4 w-4"
                  style={{ color: '#21A691' }}
                />
                <span 
                  className="text-sm font-medium"
                  style={{ color: '#21A691' }}
                >
                  {t('transcription.processing')}
                </span>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {confidence && (
              <span 
                className="text-xs font-medium"
                style={{ color: confidenceColor }}
              >
                {Math.round(confidence * 100)}%
              </span>
            )}
            
            <button
              onClick={onClose}
              className="p-1 rounded-full hover:bg-gray-100 transition-colors"
              style={{ color: '#666666' }}
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Audio Level Visualization */}
        {isRecording && (
          <div className="mb-3">
            <div className="flex items-center justify-center space-x-1 h-8">
              {[...Array(20)].map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-red-500 rounded-sm transition-all duration-100"
                  style={{
                    height: `${Math.max(2, (audioLevel + Math.random() * 20) * 0.3)}px`,
                    opacity: Math.random() > 0.3 ? 1 : 0.3
                  }}
                ></div>
              ))}
            </div>
          </div>
        )}

        {/* Live Transcript Display */}
        <div className="min-h-[80px] mb-3">
          <div 
            className="p-3 rounded-lg border-2 min-h-[80px]"
            style={{
              borderColor: '#E5E5E5',
              backgroundColor: '#F9F9F9'
            }}
          >
            {/* Final transcript (stable) */}
            {finalTranscript && (
              <span 
                className="font-medium"
                style={{ color: '#27403E' }}
              >
                {finalTranscript}
              </span>
            )}
            
            {/* Partial transcript (real-time, less confident) */}
            {partialTranscript && (
              <span 
                className="italic opacity-70"
                style={{ color: '#666666' }}
              >
                {finalTranscript ? ' ' : ''}{partialTranscript}
              </span>
            )}
            
            {/* Placeholder when no transcript */}
            {!finalTranscript && !partialTranscript && (
              <span 
                className="text-sm italic"
                style={{ color: '#999999' }}
              >
                {isRecording ? t('transcription.listening') : t('transcription.processing')}
              </span>
            )}
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex justify-between items-center">
          <div className="text-xs" style={{ color: '#999999' }}>
            {isRecording ? t('transcription.tap_to_stop') : t('transcription.processing_audio')}
          </div>
          
          {isRecording && (
            <button
              onClick={onStop}
              className="flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors"
              style={{
                backgroundColor: '#FF0000',
                color: '#FFFFFF'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#CC0000';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#FF0000';
              }}
            >
              <StopIcon className="h-4 w-4" />
              <span className="text-sm font-medium">{t('transcription.stop')}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
