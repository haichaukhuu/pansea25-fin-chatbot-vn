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
  type: string;
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
  private onError: (error: string) => void;
  private onStatusChange: (status: string) => void;
  private debugMode: boolean = false;

  // Audio processing configuration
  private static readonly CHUNK_DURATION_MS = 100; // 100ms chunks (50-200ms recommended)
  private static readonly SAMPLE_RATE = 16000; // 16kHz sample rate
  private static readonly BYTES_PER_SAMPLE = 2; // 16-bit = 2 bytes
  private static readonly MAX_CHUNK_SIZE = 32 * 1024; // 32KB AWS limit

  // Supported languages for transcription
  static readonly SUPPORTED_LANGUAGES: LanguageConfig[] = [
    { code: 'en-US', name: 'English (US)', country: 'US' },
    { code: 'vi-VN', name: 'Vietnamese', country: 'VN' }
  ];

  constructor(
    onTranscriptionResult: (result: TranscriptionResult) => void,
    onError: (error: string) => void,
    onStatusChange: (status: string) => void
  ) {
    this.onTranscriptionResult = onTranscriptionResult;
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

      // Connect to WebSocket
      const wsUrl = `ws://localhost:8000/api/transcription/stream`;
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log('WebSocket connected');
        // Send configuration
        this.websocket?.send(JSON.stringify({
          language_code: config.language_code || 'en-US',
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
        this.onError('Connection error occurred');
      };

      this.websocket.onclose = () => {
        console.log('WebSocket closed');
        this.cleanup();
      };

      // Set up MediaRecorder for audio capture
      this.setupMediaRecorder();

    } catch (error) {
      console.error('Error starting recording:', error);
      this.onError(`Failed to start recording: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
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
      // Create AudioContext for processing
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Create audio source from microphone stream
      const source = this.audioContext.createMediaStreamSource(this.audioStream!);
      
      // Create processor for chunking audio - use 4096 buffer size for better control
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      
      let audioBuffer: Float32Array[] = [];
      const sampleRate = TranscriptionService.SAMPLE_RATE; // Use configured sample rate
      const chunkDurationMs = TranscriptionService.CHUNK_DURATION_MS; // Use configured duration
      const samplesPerChunk = Math.floor((sampleRate * chunkDurationMs) / 1000);
      
      this.processor.onaudioprocess = (event) => {
        if (!this.isRecording) return;
        
        const inputBuffer = event.inputBuffer;
        const inputData = inputBuffer.getChannelData(0);
        
        // Resample to 16kHz if needed
        const resampledData = this.resampleTo16kHz(inputData, inputBuffer.sampleRate);
        audioBuffer.push(resampledData);
        
        // Calculate total samples collected
        const totalSamples = audioBuffer.reduce((sum, chunk) => sum + chunk.length, 0);
        
        if (totalSamples >= samplesPerChunk) {
          // Combine buffer chunks
          const combinedBuffer = new Float32Array(totalSamples);
          let offset = 0;
          for (const chunk of audioBuffer) {
            combinedBuffer.set(chunk, offset);
            offset += chunk.length;
          }
          
          // Extract exact chunk size and save remainder
          const chunkToSend = combinedBuffer.slice(0, samplesPerChunk);
          const remainder = combinedBuffer.slice(samplesPerChunk);
          
          // Convert to PCM 16-bit format
          const pcmData = this.convertToPCM16(chunkToSend);
          
          // Send the chunk
          this.sendPCMAudioChunk(pcmData);
          
          // Reset buffer with remainder
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
      // Convert float [-1, 1] to 16-bit PCM
      const sample = Math.max(-1, Math.min(1, floatData[i]));
      const pcmSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
      view.setInt16(i * TranscriptionService.BYTES_PER_SAMPLE, pcmSample, true); // little-endian
    }
    
    return new Uint8Array(buffer);
  }

  private async sendPCMAudioChunk(pcmData: Uint8Array) {
    try {
      // Debug logging
      if (this.debugMode) {
        const chunkSizeKB = (pcmData.length / 1024).toFixed(2);
        console.log(`Sending audio chunk: ${pcmData.length} bytes (${chunkSizeKB} KB)`);
      }
      
      // Validate chunk size before sending
      if (pcmData.length > TranscriptionService.MAX_CHUNK_SIZE) {
        console.warn(`Chunk size ${pcmData.length} exceeds recommended limit ${TranscriptionService.MAX_CHUNK_SIZE}`);
      }

      // Convert to base64 for WebSocket transmission
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
    switch (data.type) {
      case 'session_started':
        this.sessionId = data.session_id || null;
        console.log('Transcription session started:', this.sessionId);
        break;

      case 'transcription_result':
        if (data.result) {
          this.onTranscriptionResult(data.result);
        }
        break;

      case 'error':
        this.onError(data.error_message || 'Unknown transcription error');
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }

  stopRecording() {
    try {
      if (this.isRecording) {
        this.isRecording = false;
        this.onStatusChange('stopping');
      }

      // Send end session message
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({
          type: 'end_session'
        }));
      }

      this.cleanup();
    } catch (error) {
      console.error('Error stopping recording:', error);
    }
  }

  private cleanup() {
    // Stop audio processing
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    // Stop media recorder (fallback if still using it)
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }

    // Stop audio stream
    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
      this.audioStream = null;
    }

    // Close WebSocket
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }

    this.isRecording = false;
    this.sessionId = null;
    this.onStatusChange('stopped');
  }

  getIsRecording(): boolean {
    return this.isRecording;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }
}
