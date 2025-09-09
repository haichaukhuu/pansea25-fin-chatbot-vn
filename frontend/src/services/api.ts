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

export interface RegisterRequest {
  email: string;
  password: string;
  display_name?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

export interface UserResponse {
  id: string;
  email: string;
  display_name?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  user?: T;
  access_token?: string;
}

// User Preferences interfaces
export interface UserPreferences {
  agriculturalActivity: string[];
  cropType: string;
  livestockType: string;
  location: string;
  farmScale: string;
  supportNeeds: string[];
  financialKnowledge: string;
}

export interface PreferenceCreateRequest {
  questionnaire_answer: UserPreferences;
}

export interface PreferenceUpdateRequest {
  questionnaire_answer?: UserPreferences;
}

export interface UserPreferenceData {
  user_id: string;
  user_email: string;
  questionnaire_answer: UserPreferences;
  recorded_on: string;
  updated_on: string;
}

export interface PreferenceResponse {
  success: boolean;
  message: string;
  data?: UserPreferenceData;
}

class ApiService {
  private baseUrl: string;
  private abortController: AbortController | null = null;

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
    
    // Create a new abort controller for this request
    this.abortController = new AbortController();
    
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
        signal: this.abortController.signal,
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
      if (error instanceof Error && error.name === 'AbortError') {
        // Request was aborted by user
        console.log('Streaming request was stopped by user');
        onComplete(); // Treat abort as completion
      } else {
        console.error('Streaming request failed:', error);
        onError(error instanceof Error ? error : new Error(String(error)));
      }
    } finally {
      this.abortController = null;
    }
  }

  // Stop the current streaming request
  stopStreaming(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
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
  async login(request: LoginRequest): Promise<ApiResponse<UserResponse>> {
    try {
      const loginResponse = await this.request<LoginResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      
      // After successful login, get user profile
      const userResponse = await this.request<UserResponse>('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${loginResponse.access_token}`,
        },
      });
      
      return { 
        success: true, 
        user: userResponse,
        access_token: loginResponse.access_token 
      };
    } catch (error: any) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        message: error.message || 'Login failed' 
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
      const response = await this.request<UserResponse>('/api/auth/me', {
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

  async logout(): Promise<ApiResponse> {
    try {
      await this.request<any>('/api/auth/logout', {
        method: 'POST',
      });
      return { success: true };
    } catch (error: any) {
      console.error('Logout failed:', error);
      return { 
        success: false, 
        message: error.message || 'Logout failed' 
      };
    }
  }

  // User Preferences methods
  async createPreferences(preferences: UserPreferences): Promise<ApiResponse<PreferenceResponse>> {
    try {
      const requestData: PreferenceCreateRequest = {
        questionnaire_answer: preferences
      };
      
      const response = await this.request<PreferenceResponse>('/api/preferences/', {
        method: 'POST',
        body: JSON.stringify(requestData),
      });
      
      return { 
        success: response.success, 
        message: response.message,
        user: response
      };
    } catch (error: any) {
      console.error('Create preferences failed:', error);
      return { 
        success: false, 
        message: error.message || 'Failed to save preferences' 
      };
    }
  }

  async getPreferences(): Promise<ApiResponse<PreferenceResponse>> {
    try {
      const response = await this.request<PreferenceResponse>('/api/preferences/');
      return { 
        success: response.success, 
        message: response.message,
        user: response
      };
    } catch (error: any) {
      console.error('Get preferences failed:', error);
      return { 
        success: false, 
        message: error.message || 'Failed to get preferences' 
      };
    }
  }

  async updatePreferences(preferences: UserPreferences): Promise<ApiResponse<PreferenceResponse>> {
    try {
      const requestData: PreferenceUpdateRequest = {
        questionnaire_answer: preferences
      };
      
      const response = await this.request<PreferenceResponse>('/api/preferences/', {
        method: 'PUT',
        body: JSON.stringify(requestData),
      });
      
      return { 
        success: response.success, 
        message: response.message,
        user: response
      };
    } catch (error: any) {
      console.error('Update preferences failed:', error);
      return { 
        success: false, 
        message: error.message || 'Failed to update preferences' 
      };
    }
  }

  async deletePreferences(): Promise<ApiResponse<PreferenceResponse>> {
    try {
      const response = await this.request<PreferenceResponse>('/api/preferences/', {
        method: 'DELETE',
      });
      
      return { 
        success: response.success, 
        message: response.message,
        user: response
      };
    } catch (error: any) {
      console.error('Delete preferences failed:', error);
      return { 
        success: false, 
        message: error.message || 'Failed to delete preferences' 
      };
    }
  }

  async upsertPreferences(preferences: UserPreferences): Promise<ApiResponse<PreferenceResponse>> {
    try {
      const requestData: PreferenceCreateRequest = {
        questionnaire_answer: preferences
      };
      
      const response = await this.request<PreferenceResponse>('/api/preferences/upsert', {
        method: 'POST',
        body: JSON.stringify(requestData),
      });
      
      return { 
        success: response.success, 
        message: response.message,
        user: response
      };
    } catch (error: any) {
      console.error('Upsert preferences failed:', error);
      return { 
        success: false, 
        message: error.message || 'Failed to save preferences' 
      };
    }
  }

  async checkPreferencesExist(): Promise<{ exists: boolean; user_id: string; message: string }> {
    try {
      const response = await this.request<{ exists: boolean; user_id: string; message: string }>('/api/preferences/exists');
      return response;
    } catch (error: any) {
      console.error('Check preferences existence failed:', error);
      return { 
        exists: false, 
        user_id: '', 
        message: error.message || 'Failed to check preferences' 
      };
    }
  }

  async getPreferencesHealth(): Promise<any> {
    try {
      const response = await this.request<any>('/api/preferences/health');
      return response;
    } catch (error: any) {
      console.error('Preferences health check failed:', error);
      return { 
        status: 'unhealthy', 
        error: error.message || 'Health check failed' 
      };
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export the class for testing
export { ApiService };
