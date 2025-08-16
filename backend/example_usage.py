#!/usr/bin/env python3
"""
Example Usage of AI Models

This script shows practical examples of how to use the AI models
for building a financial literacy chatbot.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AI models
from ai_models import ModelFactory, ModelManager, ModelName

async def simple_chat_example():
    """Simple chat example with the Gemini model"""
    print("=== Simple Chat Example (Gemini) ===")
    
    try:
        # Create Gemini model
        gemini = ModelFactory.create_gemini_model()
        
        # Simple question
        question = "Xin chào, tôi muốn biết về lãi suất tiết kiệm ngân hàng"
        response = await gemini.generate_response(question)
        
        print(f"User: {question}")
        print(f"Bot: {response.content}")
        print(f"Model: {response.model_used}")
        
    except Exception as e:
        print(f"Error: {e}")

async def gemma_chat_example():
    """Simple chat example with the Gemma model"""
    print("\n=== Simple Chat Example (Gemma) ===")
    
    try:
        # Create Gemma model
        gemma = ModelFactory.create_gemma_model(ModelName.GEMMA_3N_2B)
        
        # Simple question
        question = "Xin chào, tôi muốn biết về lãi suất vay nông nghiệp"
        response = await gemma.generate_response(question)
        
        print(f"User: {question}")
        print(f"Bot: {response.content}")
        print(f"Model: {response.model_used}")
        print(f"Model Type: {gemma.get_model_type()}")
        
    except Exception as e:
        print(f"Error: {e}")

async def context_aware_chat():
    """Chat with context awareness"""
    print("\n=== Context-Aware Chat Example ===")
    
    try:
        # Create Gemini model for context-aware chat
        gemini = ModelFactory.create_gemini_model()
        
        # User profile and context
        context = {
            "user_profile": {
                "location": "An Giang",
                "farming_type": "nuôi tôm",
                "experience": "5 năm"
            },
            "chat_history": [
                {"role": "user", "content": "Tôi muốn vay tiền để mở rộng ao nuôi tôm"},
                {"role": "bot", "content": "Tôi hiểu bạn muốn vay tiền để mở rộng ao nuôi tôm. Bạn có thể cho tôi biết thêm về kế hoạch của bạn không?"}
            ]
        }
        
        # Follow-up question with context
        question = "Vậy lãi suất vay sẽ là bao nhiêu và tôi cần chuẩn bị những gì?"
        
        response = await gemini.generate_response(question, context=context)
        
        print(f"User Profile: {context['user_profile']}")
        print(f"Chat History: {len(context['chat_history'])} messages")
        print(f"User: {question}")
        print(f"Bot: {response.content}")
        
    except Exception as e:
        print(f"Error: {e}")

async def rag_example():
    """Example of using models with RAG context"""
    print("\n=== RAG Context Example ===")
    
    try:
        # Create models
        gemini = ModelFactory.create_gemini_model()
        embedding_model = ModelFactory.create_embedding_model()
        
        # Simulate RAG context (in real app, this would come from vector search)
        rag_context = """
        Thông tin về vay nông nghiệp:
        - Lãi suất: 6-8% mỗi năm
        - Hạn mức: Tối đa 500 triệu VND
        - Thời hạn: 1-5 năm
        - Điều kiện: Có đất canh tác, kế hoạch sản xuất rõ ràng
        - Hồ sơ cần thiết: CMND, sổ đỏ, kế hoạch sản xuất, báo cáo tài chính
        """
        
        # Generate embedding for the context (for demonstration)
        context_embedding = await embedding_model.generate_embedding(rag_context)
        print(f"Generated embedding for RAG context: {len(context_embedding)} dimensions")
        
        # Use RAG context in response
        context = {"rag_context": rag_context}
        question = "Tôi muốn vay 200 triệu để mua máy cày, có được không?"
        
        response = await gemini.generate_response(question, context=context)
        
        print(f"RAG Context: {rag_context[:100]}...")
        print(f"User: {question}")
        print(f"Bot: {response.content}")
        
    except Exception as e:
        print(f"Error: {e}")

async def streaming_chat():
    """Example of streaming chat responses"""
    print("\n=== Streaming Chat Example ===")
    
    try:
        # Create Gemini model
        gemini = ModelFactory.create_gemini_model()
        
        question = "Hãy giải thích chi tiết về các loại bảo hiểm nông nghiệp và lợi ích của chúng"
        
        print(f"User: {question}")
        print("Bot: ", end="", flush=True)
        
        # Stream the response
        async for chunk in gemini.generate_streaming_response(question):
            print(chunk, end="", flush=True)
        
        print()  # New line after streaming
        
    except Exception as e:
        print(f"Error: {e}")

async def model_comparison():
    """Compare different models"""
    print("\n=== Model Comparison Example ===")
    
    try:
        # Create different models
        gemini_pro = ModelFactory.create_gemini_model(ModelName.GEMINI_PRO)
        gemma_2b = ModelFactory.create_gemma_model(ModelName.GEMMA_3N_2B)
        
        question = "Giải thích ngắn gọn về lãi suất kép"
        
        print(f"Question: {question}")
        
        # Test Gemini Pro
        print(f"\n--- {gemini_pro.config.name} ---")
        response_gemini = await gemini_pro.generate_response(question)
        print(f"Response: {response_gemini.content[:200]}...")
        
        # Test Gemma 2B
        print(f"\n--- {gemma_2b.config.name} ---")
        response_gemma = await gemma_2b.generate_response(question)
        print(f"Response: {response_gemma.content[:200]}...")
        
    except Exception as e:
        print(f"Error: {e}")

async def model_manager_example():
    """Example using the model manager"""
    print("\n=== Model Manager Example ===")
    
    try:
        # Create model manager
        manager = await ModelManager.create_default_manager()
        
        # Get model status
        status = manager.get_model_status()
        print("Model Status:")
        for name, info in status.items():
            print(f"  {name}: {info['type']} - {'Available' if info['is_available'] else 'Unavailable'}")
        
        # Use unified interface
        question = "Tôi muốn biết về đầu tư vào công nghệ nông nghiệp"
        
        print(f"\nUser: {question}")
        print("Bot: ", end="", flush=True)
        
        # Generate streaming response through manager
        async for chunk in manager.generate_streaming_response(question):
            print(chunk, end="", flush=True)
        
        print()  # New line after streaming
        
        # Stop health monitoring
        manager.stop_health_monitoring()
        
    except Exception as e:
        print(f"Error: {e}")

async def main():
    """Main function to run all examples"""
    print("🚀 AI Models Usage Examples")
    print("Make sure you have set GOOGLE_GENAI_API_KEY environment variable")
    
    # Check if API key is available
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_GENAI_API_KEY environment variable not set!")
        print("Please set it with your Google GenAI API key to run the examples.")
        return
    
    print(f"✓ Found Google GenAI API key: {api_key[:10]}...")
    
    try:
        # Run examples
        await simple_chat_example()
        await gemma_chat_example()
        await context_aware_chat()
        await rag_example()
        await streaming_chat()
        await model_comparison()
        await model_manager_example()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Examples failed with error: {e}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
