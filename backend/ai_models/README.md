# AI Models for Financial Literacy Chatbot

This module provides a clean, testable interface for AI models used in the financial literacy chatbot for Vietnamese smallholder farmers.

## Overview

The AI models module is designed with the following principles:
- **Clean Architecture**: Clear separation of concerns with base classes and implementations
- **LangChain Integration**: Built on top of LangChain for better LLM management
- **Async Support**: Full async/await support for better performance
- **Health Monitoring**: Built-in health checks and fallback mechanisms
- **Easy Testing**: Simple interfaces for testing individual models and the entire system
- **Multi-Model Support**: Support for both Gemini and Gemma models through unified interface

## Architecture

```
ai_models/
├── __init__.py              # Module exports
├── base_model.py            # Abstract base classes and interfaces
├── google_genai_model.py    # Generalized Google GenAI implementation (Gemini + Gemma)
├── embedding_model.py       # Multilingual embedding model
├── model_factory.py         # Factory for creating models
├── model_manager.py         # Manager for orchestrating multiple models
└── README.md               # This file
```

## Models

### 1. Google GenAI Models (`google_genai_model.py`)
- **Purpose**: Primary LLM for generating responses (supports both Gemini and Gemma)
- **Features**: 
  - Vietnamese language support
  - Context-aware responses
  - Streaming responses
  - System prompt customization
  - Automatic model type detection
- **Supported Models**:
  - **Gemini**: `gemini-pro`, `gemini-1.5-flash`, `gemini-pro-vision`
  - **Gemma**: `gemma-3n-2b-it`, `gemma-3n-8b-it`, `gemma-2b-it`, `gemma-7b-it`
- **Configuration**: Temperature, max tokens, capabilities

### 2. Embedding Model (`embedding_model.py`)
- **Purpose**: Generate embeddings for RAG system
- **Features**:
  - Multilingual support (Vietnamese + English)
  - Query vs passage embeddings
  - Batch processing
- **Model**: `intfloat/multilingual-E5-large` (1024 dimensions)

## Key Components

### BaseModel
Abstract base class defining the interface for all AI models:
- `generate_response()` - Generate text responses
- `generate_streaming_response()` - Stream responses
- `generate_embedding()` - Generate embeddings
- `health_check()` - Check model health

### ModelFactory
Factory class for creating models with predefined configurations:
- `create_google_genai_model()` - Create any Google GenAI model (Gemini or Gemma)
- `create_gemini_model()` - Create Gemini models (alias for backward compatibility)
- `create_gemma_model()` - Create Gemma models
- `create_embedding_model()` - Create embedding models
- `create_default_models()` - Create all default models

### ModelManager
Orchestrates multiple models with fallback and health monitoring:
- Unified interface for all model types
- Automatic fallback to backup models
- Health monitoring and error handling
- Model status tracking

## Usage Examples

### Basic Usage

```python
from ai_models import ModelFactory, ModelManager, ModelName

# Create individual models
gemini = ModelFactory.create_gemini_model()
gemma = ModelFactory.create_gemma_model(ModelName.GEMMA_3N_2B)
embedding_model = ModelFactory.create_embedding_model()

# Or use the manager
manager = await ModelManager.create_default_manager()
```

### Creating Specific Models

```python
# Create Gemini models
gemini_pro = ModelFactory.create_gemini_model(ModelName.GEMINI_PRO)
gemini_flash = ModelFactory.create_gemini_model(ModelName.GEMINI_FLASH)

# Create Gemma models
gemma_2b = ModelFactory.create_gemma_model(ModelName.GEMMA_3N_2B)
gemma_8b = ModelFactory.create_gemma_model(ModelName.GEMMA_3N_8B)

# Create any Google GenAI model
any_model = ModelFactory.create_google_genai_model(ModelName.GEMMA_7B)
```

### Simple Chat

```python
# Simple question with Gemini
response = await gemini.generate_response("Xin chào, tôi muốn biết về lãi suất vay nông nghiệp")
print(response.content)

# Simple question with Gemma
response = await gemma.generate_response("Xin chào, tôi muốn biết về lãi suất tiết kiệm")
print(response.content)

# With context
context = {
    "user_profile": {"location": "Đồng Tháp", "farming_type": "trồng lúa"},
    "rag_context": "Lãi suất vay nông nghiệp: 6-8% mỗi năm"
}

response = await gemini.generate_response(
    "Tôi muốn vay 50 triệu, lãi suất sẽ là bao nhiêu?",
    context=context
)
```

### Streaming Responses

```python
# Stream response from Gemini
async for chunk in gemini.generate_streaming_response("Giải thích về bảo hiểm nông nghiệp"):
    print(chunk, end="", flush=True)

# Stream response from Gemma
async for chunk in gemma.generate_streaming_response("Lợi ích của việc tiết kiệm tiền"):
    print(chunk, end="", flush=True)
```

### Embeddings

```python
# Generate embedding
embedding = await embedding_model.generate_embedding("Lãi suất vay nông nghiệp")

# Batch processing
documents = ["Vay nông nghiệp", "Tiết kiệm tiền", "Đầu tư nông nghiệp"]
embeddings = await embedding_model.embed_documents(documents)
```

### Using Model Manager

```python
# Unified interface
response = await manager.generate_response("Câu hỏi của bạn")
embedding = await manager.generate_embedding("Văn bản cần embedding")

# Get model status
status = manager.get_model_status()
for name, info in status.items():
    print(f"{name}: {info['type']} - {'Available' if info['is_available'] else 'Unavailable'}")
```

## Configuration

### Environment Variables
```bash
GOOGLE_GENAI_API_KEY=your_google_genai_api_key_here
```

### Model Configuration
Models can be configured with custom parameters:

```python
custom_config = {
    "temperature": 0.5,
    "max_tokens": 4096,
    "is_primary": True
}

gemini = ModelFactory.create_gemini_model(
    model_name=ModelName.GEMINI_PRO,
    custom_config=custom_config
)
```

## Testing

### Run Tests
```bash
# Test all models
python test_ai_models.py

# Run examples
python example_usage.py
```

### Test Individual Components
```python
# Test Gemini model
await test_gemini_model()

# Test Gemma model
await test_gemma_model()

# Test embedding model
await test_embedding_model()

# Test model manager
await test_model_manager()

# Test model factory
await test_model_factory()
```

## Health Monitoring

The system includes automatic health monitoring:
- Periodic health checks (every 5 minutes)
- Automatic error tracking
- Model fallback on failures
- Health status reporting

```python
# Start health monitoring
await manager.start_health_monitoring()

# Check health manually
health_status = await manager.health_check_all()

# Stop monitoring
manager.stop_health_monitoring()
```

## Error Handling

The system includes robust error handling:
- Automatic retry with fallback models
- Error counting and model disabling
- Graceful degradation
- Detailed error logging

## Model Capabilities

### Gemini Models
- **GEMINI_PRO**: Full-featured model with reasoning, tool calling, and long context
- **GEMINI_FLASH**: Fast, efficient model for quick responses
- **GEMINI_PRO_VISION**: Vision-capable model for image understanding

### Gemma Models
- **GEMMA_3N_2B**: Efficient 2B parameter model for fast responses
- **GEMMA_3N_8B**: Balanced 8B parameter model with good performance
- **GEMMA_2B**: Lightweight 2B parameter model
- **GEMMA_7B**: High-quality 7B parameter model

## Future Enhancements

- **Model Caching**: Cache responses for common queries
- **Rate Limiting**: Implement rate limiting for API calls
- **Metrics Collection**: Collect usage and performance metrics
- **A/B Testing**: Support for testing different model configurations
- **Custom Models**: Support for fine-tuned models
- **Additional Providers**: Support for other AI providers

## Dependencies

- `langchain` - LLM framework
- `langchain-google-genai` - Google GenAI integration
- `sentence-transformers` - Embedding models
- `google-generativeai` - Google AI SDK
- `pydantic` - Data validation
- `numpy` - Numerical operations

## Installation

```bash
pip install -r requirements.txt
```

## Notes

- The system is designed for Vietnamese language support
- All models support async operations
- Health monitoring runs automatically when using ModelManager
- Embedding models use the E5 prefix strategy for better performance
- System prompts are in Vietnamese for better localization
- Backward compatibility is maintained for existing GeminiModel usage
- Model type detection is automatic based on model ID
