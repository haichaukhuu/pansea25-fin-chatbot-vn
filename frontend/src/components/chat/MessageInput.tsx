import React, { useState, useRef } from 'react';
import { 
  PaperAirplaneIcon,
  PaperClipIcon,
  MicrophoneIcon
} from '@heroicons/react/24/outline';
import { useChat } from '../../context/ChatContext';

interface MessageInputProps {
  onSendMessage: (message: string) => Promise<void>;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { uploadFile } = useChat();

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
          disabled={disabled}
        >
          <PaperClipIcon className="h-5 w-5" />
        </button>

        {/* Voice input button */}
        <button
          type="button"
          onClick={handleVoiceInput}
          className="p-2 flex items-center justify-center transition-colors"
          style={{
            color: isRecording ? '#FF0000' : '#21A691',
            backgroundColor: '#eeeeee'
          }}
          onMouseEnter={(e) => {
            if (!isRecording) e.currentTarget.style.color = '#87DF2C';
          }}
          onMouseLeave={(e) => {
            if (!isRecording) e.currentTarget.style.color = '#21A691';
          }}
          title="Voice input"
          disabled={disabled}
        >
          <MicrophoneIcon className="h-5 w-5" />
        </button>

        {/* Message input */}
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          rows={1}
          disabled={disabled}
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

        {/* Send button */}
        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className="p-3 flex items-center justify-center rounded-r-lg focus:outline-none disabled:opacity-50 transition-colors font-medium"
          style={{
            backgroundColor: '#87DF2C',
            color: '#27403E'
          }}
          onMouseEnter={(e) => {
            if (!e.currentTarget.disabled) e.currentTarget.style.backgroundColor = '#7BC628';
          }}
          onMouseLeave={(e) => {
            if (!e.currentTarget.disabled) e.currentTarget.style.backgroundColor = '#87DF2C';
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
