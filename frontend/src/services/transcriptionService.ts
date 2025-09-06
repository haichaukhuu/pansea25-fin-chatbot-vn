/**
 * Transcription service for handling Amazon Transcribe integration
 */

export interface TranscriptionConfig {
  language_code?: string;
  sample_rate?: number;
  enable_partial_results?: boolean;
}

export interface LanguageConfig {
  code: string;
  name: string;
  country?: string;
}

export interface TranscriptionResult {
  transcript: string;
  confidence?: number;
  is_partial: boolean;
  start_time?: number;
  end_time?: number;
  alternatives?: string[];
}

export interface TranscriptionResponse {
  type: 'session_started' | 'transcription_result' | 'session_ended' | 'error' | string;
  status?: string;
  result?: TranscriptionResult;
  error_message?: string;
  session_id?: string;
}

export class TranscriptionService {
  private websocket: WebSocket | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioStream: MediaStream | null = null;
  private isRecording = false;
  private sessionId: string | null = null;
  private onTranscriptionResult: (result: TranscriptionResult) => void;
  private onPartialResult: (result: TranscriptionResult) => void;
  private onError: (error: string) => void;
  private onStatusChange: (status: string) => void;
  private debugMode: boolean = false;
  private shouldReconnect: boolean = false;

  // Audio processing configuration
  private static readonly CHUNK_DURATION_MS = 50; 
  private static readonly SAMPLE_RATE = 16000; // 16kHz sample rate
  private static readonly BYTES_PER_SAMPLE = 2; // 16-bit = 2 bytes
  private static readonly MAX_CHUNK_SIZE = 32 * 1024; // 32KB AWS limit 

  // Supported languages for transcription
  static readonly SUPPORTED_LANGUAGES: LanguageConfig[] = [
    { code: 'vi-VN', name: 'Vietnamese', country: 'VN' },
    { code: 'en-US', name: 'English (US)', country: 'US' }
  ];

  constructor(
    onTranscriptionResult: (result: TranscriptionResult) => void,
    onError: (error: string) => void,
    onStatusChange: (status: string) => void,
    onPartialResult?: (result: TranscriptionResult) => void
  ) {
    this.onTranscriptionResult = onTranscriptionResult;
    this.onPartialResult = onPartialResult || (() => {});
    this.onError = onError;
    this.onStatusChange = onStatusChange;
    
    // Enable debug mode if set in localStorage
    this.debugMode = localStorage.getItem('transcription-debug') === 'true';
    if (this.debugMode) {
      console.log('Transcription debug mode enabled');
    }
  }

  /**
   * Get the appropriate language code based on current app language
   */
  static getLanguageCode(appLanguage: 'vi' | 'en'): string {
    return appLanguage === 'vi' ? 'vi-VN' : 'en-US';
  }

  async startRecording(config: TranscriptionConfig = {}) {
    // Clean up any existing session before starting new session
    if (this.isRecording || this.websocket || this.audioStream) {
      console.log('Cleaning up previous session before starting new recording...');
      this.stopRecording();
      // Longer wait to ensure complete cleanup
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    let retryCount = 0;
    const maxRetries = 1; // Retry once 
  // Enable reconnects for this recording session
  this.shouldReconnect = true;
    
    const attemptConnection = async (): Promise<void> => {
      try {
        // Get user media (microphone)
        this.audioStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: config.sample_rate || 16000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
          }
        });

        const wsUrl = `ws://localhost:8000/api/transcription/stream`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
          console.log('WebSocket connected');
          // Send configuration with Vietnamese as default
          this.websocket?.send(JSON.stringify({
            language_code: config.language_code || 'vi-VN',
            sample_rate: config.sample_rate || 16000,
            enable_partial_results: config.enable_partial_results !== false
          }));
        };

        this.websocket.onmessage = (event) => {
          const data: TranscriptionResponse = JSON.parse(event.data);
          this.handleWebSocketMessage(data);
        };

        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          // attempt reconnects if didn't intentionally stop
          if (this.shouldReconnect && this.isRecording && retryCount < maxRetries) {
            retryCount++;
            console.log(`Retrying connection (${retryCount}/${maxRetries})...`);
            setTimeout(() => attemptConnection(), 1000);
          } else {
            this.onError('Connection error occurred. Please check your network and try again.');
          }
        };

        this.websocket.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          
          if (event.code === 1000) {
            // Normal closure
            console.log('WebSocket closed normally - no reconnection needed');
            this.shouldReconnect = false;
            this.cleanup();
            return;
          }
          
          // Only reconnect on unexpected closures while actively recording
          if (this.shouldReconnect && this.isRecording && retryCount < maxRetries) {
            retryCount++;
            console.log(`Connection lost unexpectedly, retrying (${retryCount}/${maxRetries})...`);
            setTimeout(() => attemptConnection(), 1000);
          } else {
            console.log('Not reconnecting - shouldReconnect:', this.shouldReconnect, 'isRecording:', this.isRecording);
            this.cleanup();
          }
        };

        // Set up MediaRecorder for audio capture
        this.setupMediaRecorder();

      } catch (error) {
        console.error('Error starting recording:', error);
        if (retryCount < maxRetries) {
          retryCount++;
          console.log(`Retrying after error (${retryCount}/${maxRetries})...`);
          setTimeout(() => attemptConnection(), 1000);
        } else {
          this.onError(`Failed to start recording: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }
    };

    await attemptConnection();
  }

  private setupMediaRecorder() {
    if (!this.audioStream) return;

    try {
      // Use AudioContext for better control over audio processing
      this.setupAudioContext();

    } catch (error) {
      console.error('Error setting up MediaRecorder:', error);
      this.onError('Failed to set up audio recording');
    }
  }

  private audioContext: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;

  private setupAudioContext() {
    try {
      // AudioContext for processing
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // audio from microphone
      const source = this.audioContext.createMediaStreamSource(this.audioStream!);
      
      // chunking audio - 4096 buffer size 
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      
      let audioBuffer: Float32Array[] = [];
      const sampleRate = TranscriptionService.SAMPLE_RATE;
      const chunkDurationMs = TranscriptionService.CHUNK_DURATION_MS; 
      const samplesPerChunk = Math.floor((sampleRate * chunkDurationMs) / 1000);
      
      this.processor.onaudioprocess = (event) => {
        if (!this.isRecording) return;
        
        const inputBuffer = event.inputBuffer;
        const inputData = inputBuffer.getChannelData(0);
        
        // Resample to 16kHz if needed
        const resampledData = this.resampleTo16kHz(inputData, inputBuffer.sampleRate);
        audioBuffer.push(resampledData);
        
        const totalSamples = audioBuffer.reduce((sum, chunk) => sum + chunk.length, 0);
        
        if (totalSamples >= samplesPerChunk) {
          const combinedBuffer = new Float32Array(totalSamples);
          let offset = 0;
          for (const chunk of audioBuffer) {
            combinedBuffer.set(chunk, offset);
            offset += chunk.length;
          }

          const chunkToSend = combinedBuffer.slice(0, samplesPerChunk);
          const remainder = combinedBuffer.slice(samplesPerChunk);
          const pcmData = this.convertToPCM16(chunkToSend);

          this.sendPCMAudioChunk(pcmData);
          audioBuffer = remainder.length > 0 ? [remainder] : [];
        }
      };
      
      // Connect the audio processing chain
      source.connect(this.processor);
      this.processor.connect(this.audioContext.destination);
      
      console.log('AudioContext setup completed');
      this.isRecording = true;
      this.onStatusChange('recording');
      
    } catch (error) {
      console.error('Error setting up AudioContext:', error);
      this.onError('Failed to set up audio processing');
    }
  }

  private resampleTo16kHz(inputData: Float32Array, inputSampleRate: number): Float32Array {
    const targetSampleRate = TranscriptionService.SAMPLE_RATE;
    if (inputSampleRate === targetSampleRate) {
      return inputData;
    }
    
    const ratio = inputSampleRate / targetSampleRate;
    const outputLength = Math.round(inputData.length / ratio);
    const output = new Float32Array(outputLength);
    
    for (let i = 0; i < outputLength; i++) {
      const sourceIndex = i * ratio;
      const lower = Math.floor(sourceIndex);
      const upper = Math.ceil(sourceIndex);
      const fraction = sourceIndex - lower;
      
      if (upper >= inputData.length) {
        output[i] = inputData[lower];
      } else {
        output[i] = inputData[lower] * (1 - fraction) + inputData[upper] * fraction;
      }
    }
    
    return output;
  }

  private convertToPCM16(floatData: Float32Array): Uint8Array {
    const buffer = new ArrayBuffer(floatData.length * TranscriptionService.BYTES_PER_SAMPLE);
    const view = new DataView(buffer);
    
    for (let i = 0; i < floatData.length; i++) {
      const sample = Math.max(-1, Math.min(1, floatData[i]));
      const pcmSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
      view.setInt16(i * TranscriptionService.BYTES_PER_SAMPLE, pcmSample, true); // little-endian
    }
    
    return new Uint8Array(buffer);
  }

  private async sendPCMAudioChunk(pcmData: Uint8Array) {
    try {
      if (this.debugMode) {
        const chunkSizeKB = (pcmData.length / 1024).toFixed(2);
        console.log(`Sending audio chunk: ${pcmData.length} bytes (${chunkSizeKB} KB)`);
      }
      
      // Handle large chunks by splitting automatically 
      if (pcmData.length > TranscriptionService.MAX_CHUNK_SIZE) {
        console.warn(`Chunk size ${pcmData.length} exceeds limit ${TranscriptionService.MAX_CHUNK_SIZE}. Auto-splitting...`);
        
        // Split into smaller chunks automatically
        const numberOfChunks = Math.ceil(pcmData.length / TranscriptionService.MAX_CHUNK_SIZE);
        for (let i = 0; i < numberOfChunks; i++) {
          const start = i * TranscriptionService.MAX_CHUNK_SIZE;
          const end = Math.min(start + TranscriptionService.MAX_CHUNK_SIZE, pcmData.length);
          const chunk = pcmData.slice(start, end);
          
          const base64Audio = btoa(String.fromCharCode(...chunk));
          
          if (this.websocket?.readyState === WebSocket.OPEN) {
            const message = {
              type: 'audio_chunk',
              audio_data: base64Audio
            };
            
            this.websocket.send(JSON.stringify(message));
            
            // Small delay between chunks to prevent overwhelming
            if (i < numberOfChunks - 1) {
              await new Promise(resolve => setTimeout(resolve, 1));
            }
          }
        }
        return;
      }

      // Send normal-sized chunk
      const base64Audio = btoa(String.fromCharCode(...pcmData));

      if (this.websocket?.readyState === WebSocket.OPEN) {
        const message = {
          type: 'audio_chunk',
          audio_data: base64Audio
        };
        
        // Debug logging for message size
        if (this.debugMode) {
          const messageSize = JSON.stringify(message).length;
          console.log(`WebSocket message size: ${messageSize} bytes`);
        }
        
        this.websocket.send(JSON.stringify(message));
      }
    } catch (error) {
      console.error('Error sending audio chunk:', error);
    }
  }

  private handleWebSocketMessage(data: TranscriptionResponse) {
    console.log('WebSocket message received:', data.type, data);
    
    switch (data.type) {
      case 'session_started':
        this.sessionId = data.session_id || null;
        console.log('Transcription session started:', this.sessionId);
        break;

      case 'transcription_result':
        if (data.result) {
          if (data.result.is_partial) {
            // Handle partial results for live display
            console.log('Handling partial result:', data.result.transcript);
            this.onPartialResult(data.result);
          } else {
            // Handle final results
            console.log('Received final transcription result:', data.result.transcript);
            this.onTranscriptionResult(data.result);
          }
        }
        break;

      case 'session_ended':
        console.log('Session ended by backend:', data.session_id);
        // Session has been properly ended by backend
        this.shouldReconnect = false;
        this.isRecording = false;
        this.onStatusChange('stopped');
        break;

      case 'error':
        console.error('Transcription error from backend:', data.error_message);
        this.onError(data.error_message || 'Unknown transcription error');
        break;

      default:
        console.log('Unknown message type:', data.type, data);
    }
  }

  stopRecording() {
    console.log('TranscriptionService: Stop recording requested');
    
    try {
      // Disable reconnects for intentional stop
      this.shouldReconnect = false;
      
      if (this.isRecording) {
        this.isRecording = false;
        this.onStatusChange('stopping');
      }

      // Send end session message BEFORE cleanup
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({
          type: 'end_session'
        }));
        console.log('Sent end_session message to backend');
        
        // Give backend time to process end_session before closing
        setTimeout(() => {
          this.cleanup();
        }, 200); // Increased delay
      } else {
        // If websocket is not open, cleanup immediately
        this.cleanup();
      }
      
    } catch (error) {
      console.error('Error stopping recording:', error);
      // Force cleanup even if there's an error
      this.cleanup();
    }
  }

  private cleanup() {
    console.log('TranscriptionService: Starting cleanup...');
    
  // Ensure reconnects are disabled during cleanup
  this.shouldReconnect = false;

    // Stop recording immediately
    this.isRecording = false;
    
    // Stop audio processing
    if (this.processor) {
      try {
        this.processor.disconnect();
      } catch (e) {
        console.warn('Error disconnecting processor:', e);
      }
      this.processor = null;
    }

    if (this.audioContext) {
      try {
        this.audioContext.close();
      } catch (e) {
        console.warn('Error closing audio context:', e);
      }
      this.audioContext = null;
    }

    // Stop media recorder (fallback if still using it)
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch (e) {
        console.warn('Error stopping media recorder:', e);
      }
    }
    this.mediaRecorder = null;

    // Stop audio stream
    if (this.audioStream) {
      try {
        this.audioStream.getTracks().forEach(track => {
          track.stop();
          console.log('Stopped audio track:', track.label);
        });
      } catch (e) {
        console.warn('Error stopping audio tracks:', e);
      }
      this.audioStream = null;
    }

    // Close WebSocket and send end session if connected
    if (this.websocket) {
      try {
        if (this.websocket.readyState === WebSocket.OPEN) {
          this.websocket.send(JSON.stringify({
            type: 'end_session'
          }));
        }
        // Close with normal closure code to signal intentional shutdown
        try {
          this.websocket.close(1000, 'Normal Closure');
        } catch {
          // Fallback without params if the environment rejects codes
          this.websocket.close();
        }
      } catch (e) {
        console.warn('Error closing websocket:', e);
      }
      this.websocket = null;
    }

    // Reset all state
    this.sessionId = null;
    
    console.log('TranscriptionService: Cleanup completed');
    
    // Delay status change to prevent race conditions with new sessions
    setTimeout(() => {
      if (!this.isRecording && !this.websocket) {
        this.onStatusChange('stopped');
      }
    }, 100);
  }

  getIsRecording(): boolean {
    return this.isRecording;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }
}
