import React, { useState, useRef } from 'react';
import { 
  PaperAirplaneIcon,
  PaperClipIcon,
  MicrophoneIcon
} from '@heroicons/react/24/outline';
import { useChat } from '../../context/ChatContext';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { uploadFile } = useChat();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
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
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsRecording(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setMessage(prev => prev + transcript);
        setIsRecording(false);
      };

      recognition.onerror = () => {
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognition.start();
    } else {
      alert('Speech recognition is not supported in your browser.');
    }
  };

  return (
    <div className="border-t p-4 shadow-lg" style={{ borderColor: '#21A691', backgroundColor: '#FFFFFF' }}>
      <form onSubmit={handleSubmit} className="flex items-end space-x-3">
        {/* File upload button */}
        <div className="flex space-x-1">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-2 rounded-lg transition-colors border"
            style={{
              color: '#21A691',
              borderColor: '#21A691',
              backgroundColor: 'transparent'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#21A691';
              e.currentTarget.style.color = '#FFFFFF';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#21A691';
            }}
            title="Upload file"
            disabled={disabled}
          >
            <PaperClipIcon className="h-5 w-5" />
          </button>
          <button
            type="button"
            onClick={handleVoiceInput}
            className="p-2 rounded-lg transition-colors border"
            style={{
              color: isRecording ? '#FF0000' : '#21A691',
              backgroundColor: isRecording ? '#FFE5E5' : 'transparent',
              borderColor: isRecording ? '#FF0000' : '#21A691'
            }}
            onMouseEnter={(e) => {
              if (!isRecording) {
                e.currentTarget.style.backgroundColor = '#21A691';
                e.currentTarget.style.color = '#FFFFFF';
              }
            }}
            onMouseLeave={(e) => {
              if (!isRecording) {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = '#21A691';
              }
            }}
            title="Voice input"
            disabled={disabled}
          >
            <MicrophoneIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Message input */}
        <div className="flex-1 relative">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            rows={1}
            disabled={disabled}
            className="w-full px-4 py-2 border-2 rounded-lg focus:outline-none focus:ring-2 resize-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            style={{
              minHeight: '42px',
              maxHeight: '120px',
              height: 'auto',
              backgroundColor: '#FFFFFF',
              borderColor: '#21A691',
              color: '#27403E'
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = '#87DF2C';
              e.currentTarget.style.boxShadow = '0 0 0 2px rgba(135, 223, 44, 0.2)';
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = '#21A691';
              e.currentTarget.style.boxShadow = 'none';
            }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = Math.min(target.scrollHeight, 120) + 'px';
            }}
          />
        </div>

        {/* Send button */}
        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className="p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium shadow-md"
          style={{
            backgroundColor: '#87DF2C',
            color: '#27403E'
          }}
          onMouseEnter={(e) => {
            if (!e.currentTarget.disabled) {
              e.currentTarget.style.backgroundColor = '#7BC628';
            }
          }}
          onMouseLeave={(e) => {
            if (!e.currentTarget.disabled) {
              e.currentTarget.style.backgroundColor = '#87DF2C';
            }
          }}
          onFocus={(e) => {
            e.currentTarget.style.boxShadow = '0 0 0 2px rgba(135, 223, 44, 0.3)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.boxShadow = 'none';
          }}
          title="Send message"
        >
          <PaperAirplaneIcon className="h-5 w-5" />
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

      {isRecording && (
        <div className="mt-2 flex items-center space-x-2" style={{ color: '#FF0000' }}>
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: '#FF0000' }}></div>
          <span className="text-sm">Recording...</span>
        </div>
      )}
    </div>
  );
};
