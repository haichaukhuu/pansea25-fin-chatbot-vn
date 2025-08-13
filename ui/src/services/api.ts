// API service for communicating with the AgriFinHub backend

const API_BASE_URL = 'http://localhost:8000';

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
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
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
}

// Export singleton instance
export const apiService = new ApiService();

// Export the class for testing
export { ApiService };
