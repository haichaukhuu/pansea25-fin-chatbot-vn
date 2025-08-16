// API service for communicating with the AgriFinHub backend

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'bot';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  chat_history?: ChatMessage[];
  user_profile?: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  model_used: string;
  confidence_score: number;
  usage_stats: Record<string, any>;
}

export interface HealthResponse {
  status: string;
  models: Record<string, boolean>;
  message: string;
}

// Authentication interfaces
export interface LoginRequest {
  email: string;
  password: string;
}

export interface GoogleLoginRequest {
  id_token: string;
  email: string;
  name: string;
  avatar?: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
}

export interface AuthResponse {
  uid: string;
  email: string;
  display_name?: string;
  photo_url?: string;
  email_verified: boolean;
  id_token: string;
  refresh_token: string;
  expires_in: string;
  provider?: string;
}

export interface UserResponse {
  uid: string;
  email: string;
  display_name?: string;
  photo_url?: string;
  email_verified: boolean;
  created_at?: number;
  last_sign_in?: number;
  provider?: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  user?: T;
  access_token?: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Get auth token from localStorage if it exists
    const token = localStorage.getItem('authToken');
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // Send chat message
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Send streaming chat message
  async sendStreamingMessage(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): Promise<void> {
    const url = `${this.baseUrl}/chat/stream`;
    
    // Get auth token from localStorage if it exists
    const token = localStorage.getItem('authToken');
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last incomplete line in buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'content') {
                onChunk(data.content);
              } else if (data.type === 'done') {
                onComplete();
                return;
              } else if (data.type === 'error') {
                throw new Error(data.message || 'Streaming error');
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line, parseError);
            }
          }
        }
      }
      
      onComplete();
    } catch (error) {
      console.error('Streaming request failed:', error);
      onError(error instanceof Error ? error : new Error(String(error)));
    }
  }

  // Get available models
  async getModels(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>('/models');
  }

  // Test connection
  async testConnection(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch (error) {
      console.error('Backend connection failed:', error);
      return false;
    }
  }

  // Authentication methods
  async login(request: LoginRequest): Promise<ApiResponse<AuthResponse>> {
    try {
      const response = await this.request<AuthResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return { success: true, user: response, access_token: response.id_token };
    } catch (error: any) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        message: error.message || 'Login failed' 
      };
    }
  }

  async loginWithGoogle(request: GoogleLoginRequest): Promise<ApiResponse<AuthResponse>> {
    try {
      const response = await this.request<AuthResponse>('/api/auth/google', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return { success: true, user: response, access_token: response.id_token };
    } catch (error: any) {
      console.error('Google login failed:', error);
      return { 
        success: false, 
        message: error.message || 'Google login failed' 
      };
    }
  }

  async register(request: RegisterRequest): Promise<ApiResponse<UserResponse>> {
    try {
      const response = await this.request<UserResponse>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return { success: true, user: response };
    } catch (error: any) {
      console.error('Registration failed:', error);
      return { 
        success: false, 
        message: error.message || 'Registration failed' 
      };
    }
  }

  async verifyToken(token: string): Promise<ApiResponse<UserResponse>> {
    try {
      const response = await this.request<UserResponse>('/api/auth/verify', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return { success: true, user: response };
    } catch (error: any) {
      console.error('Token verification failed:', error);
      return { 
        success: false, 
        message: error.message || 'Token verification failed' 
      };
    }
  }

  async getCurrentUser(): Promise<ApiResponse<UserResponse>> {
    try {
      const response = await this.request<UserResponse>('/api/auth/me');
      return { success: true, user: response };
    } catch (error: any) {
      console.error('Get current user failed:', error);
      return { 
        success: false, 
        message: error.message || 'Failed to get current user' 
      };
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export the class for testing
export { ApiService };
