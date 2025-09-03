import React, { useState } from 'react';
import { 
  CheckIcon, 
  XMarkIcon, 
  PencilIcon 
} from '@heroicons/react/24/outline';
import { useLanguage } from '../../context/LanguageContext';

interface TranscriptionConfirmationProps {
  transcript: string;
  confidence?: number;
  onConfirm: (finalText: string) => void;
  onCancel: () => void;
  isVisible: boolean;
}

export const TranscriptionConfirmation: React.FC<TranscriptionConfirmationProps> = ({
  transcript,
  confidence,
  onConfirm,
  onCancel,
  isVisible
}) => {
  const [editedText, setEditedText] = useState(transcript);
  const [isEditing, setIsEditing] = useState(false);
  const { t } = useLanguage();

  if (!isVisible) return null;

  const handleConfirm = () => {
    onConfirm(editedText);
  };

  const handleCancel = () => {
    setEditedText(transcript);
    setIsEditing(false);
    onCancel();
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const confidenceColor = confidence && confidence > 0.8 
    ? '#22c55e' 
    : confidence && confidence > 0.6 
      ? '#f59e0b' 
      : '#ef4444';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div 
        className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl"
        style={{ backgroundColor: '#FFFFFF' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 
            className="text-lg font-semibold"
            style={{ color: '#27403E' }}
          >
            {t('transcription.result_title')}
          </h3>
          {confidence && (
            <div className="flex items-center space-x-2">
              <span className="text-sm" style={{ color: '#666666' }}>
                {t('transcription.confidence')}
              </span>
              <span 
                className="text-sm font-medium"
                style={{ color: confidenceColor }}
              >
                {Math.round(confidence * 100)}%
              </span>
            </div>
          )}
        </div>

        {/* Transcription Content */}
        <div className="mb-6">
          <label 
            className="block text-sm font-medium mb-2"
            style={{ color: '#27403E' }}
          >
            {t('transcription.transcribed_text')}
          </label>
          
          {isEditing ? (
            <textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              className="w-full p-3 border-2 rounded-lg focus:outline-none resize-none"
              style={{
                borderColor: '#21A691',
                backgroundColor: '#F9F9F9',
                color: '#27403E'
              }}
              rows={4}
              autoFocus
            />
          ) : (
            <div 
              className="w-full p-3 border-2 rounded-lg min-h-[100px] cursor-pointer"
              style={{
                borderColor: '#E5E5E5',
                backgroundColor: '#F9F9F9',
                color: '#27403E'
              }}
              onClick={handleEdit}
            >
              {editedText || t('transcription.no_text')}
              {!isEditing && (
                <div className="flex items-center mt-2 text-sm" style={{ color: '#666666' }}>
                  <PencilIcon className="h-4 w-4 mr-1" />
                  {t('transcription.click_to_edit')}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={handleCancel}
            className="flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-lg border-2 transition-colors"
            style={{
              borderColor: '#E5E5E5',
              backgroundColor: '#FFFFFF',
              color: '#666666'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#F5F5F5';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#FFFFFF';
            }}
          >
            <XMarkIcon className="h-5 w-5" />
            <span>{t('transcription.cancel')}</span>
          </button>

          <button
            onClick={handleConfirm}
            disabled={!editedText.trim()}
            className="flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              backgroundColor: '#21A691',
              color: '#FFFFFF'
            }}
            onMouseEnter={(e) => {
              if (!e.currentTarget.disabled) {
                e.currentTarget.style.backgroundColor = '#1d9485';
              }
            }}
            onMouseLeave={(e) => {
              if (!e.currentTarget.disabled) {
                e.currentTarget.style.backgroundColor = '#21A691';
              }
            }}
          >
            <CheckIcon className="h-5 w-5" />
            <span>{t('transcription.confirm_send')}</span>
          </button>
        </div>

        {/* Helper Text */}
        <div className="mt-3 text-xs text-center" style={{ color: '#999999' }}>
          {t('transcription.edit_help')}
        </div>
      </div>
    </div>
  );
};
