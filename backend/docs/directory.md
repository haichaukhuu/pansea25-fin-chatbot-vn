```
agrifinhub/
│
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── frontend/                          # React.js Frontend
└── backend/                           # Python FastAPI Backend
    ├── app/
    │   ├── __init__.py
    │   │
    │   ├── main.py                    # FastAPI application entry
    │   ├── config.py                  # Configuration management
    │   ├── dependencies.py            # Dependency injection
    │   │
    │   ├── core/                      # Core business logic
    │   │   ├── __init__.py
    │   │   ├── security.py            # Firebase auth integration
    │   │   ├── database.py            # Database connections
    │   │   └── redis_client.py        # Redis client
    │   │
    │   ├── api/                       # API routes
    │   │   ├── __init__.py
    │   │   ├── v1/
    │   │   │   ├── __init__.py
    │   │   │   ├── auth.py            # Authentication endpoints
    │   │   │   ├── chat.py            # Chat endpoints
    │   │   │   ├── websocket.py       # WebSocket connections
    │   │   │   └── user.py            # User management
    │   │   └── dependencies.py
    │   │
    │   ├── models/                    # Database models
    │   │   ├── __init__.py
    │   │   ├── user.py
    │   │   ├── chat.py
    │   │   ├── knowledge.py
    │   │   └── base.py
    │   │
    │   ├── agents/                    # Multi-Agent System
    │   │   ├── __init__.py
    │   │   │
    │   │   ├── base/                  # Base agent classes
    │   │   │   ├── __init__.py
    │   │   │   ├── agent.py           # Abstract base agent
    │   │   │   ├── tool.py            # Tool interface
    │   │   │   └── memory.py          # Memory management
    │   │   │
    │   │   ├── orchestrator/          # Agent orchestration
    │   │   │   ├── __init__.py
    │   │   │   ├── orchestrator.py    # Main orchestrator
    │   │   │   ├── router.py          # Request routing
    │   │   │   └── workflow.py        # Workflow management
    │   │   │
    │   │   ├── specialized/           # Specialized agents
    │   │   │   ├── __init__.py
    │   │   │   ├── intent_classifier.py
    │   │   │   ├── rag_agent.py       # RAG retrieval agent
    │   │   │   ├── web_search_agent.py
    │   │   │   ├── response_generator.py
    │   │   │   ├── context_manager.py
    │   │   │   └── knowledge_ingestion_agent.py
    │   │   │
    │   │   └── tools/                 # Agent tools
    │   │       ├── __init__.py
    │   │       ├── vector_search.py
    │   │       ├── web_scraper.py
    │   │       ├── document_parser.py
    │   │       └── vietnamese_nlp.py
    │   │
    │   ├── services/                  # Business services
    │   │   ├── __init__.py
    │   │   ├── chat_service.py
    │   │   ├── user_service.py 
    │   │   └── auth_service.py
    │   │
    │   ├── data/                      # Data processing
    │   │   ├── __init__.py
    │   │   │
    │   │   ├── ingestion/             # Data ingestion
    │   │   │   ├── __init__.py
    │   │   │   ├── scrapers/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── bank_scraper.py
    │   │   │   │   ├── government_scraper.py
    │   │   │   │   └── news_scraper.py
    │   │   │   │
    │   │   │   ├── processors/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── text_processor.py
    │   │   │   │   ├── document_processor.py
    │   │   │   │   └── vietnamese_processor.py
    │   │   │   │
    │   │   │   └── pipelines/
    │   │   │       ├── __init__.py
    │   │   │       ├── ingestion_pipeline.py
    │   │   │       └── quality_pipeline.py
    │   │   │
    │   │   ├── vector_store/          # Vector database operations
    │   │   │   ├── __init__.py
    │   │   │   ├── chroma_client.py
    │   │   │   ├── embeddings.py
    │   │   │   └── collections.py
    │   │   │
    │   │   └── cache/                 # Caching layer
    │   │       ├── __init__.py
    │   │       ├── redis_cache.py
    │   │       └── query_cache.py
    │   │
    │   ├── ai_models/        # AI Model Integration
    │   │   ├── __init__.py
    │   │   ├── base_model.py
    │   │   ├── embeddings_model.py
    │   │   ├── sea_lion_model.py
    │   │   ├── speech_models.py                # STT/TTS processing
    │   │   └── gemini_model.py
    │   │
    │   └── schemas/                   # Pydantic schemas
    │       ├── __init__.py
    │       ├── user.py
    │       ├── chat.py
    │       ├── agent.py
    │       └── knowledge.py
    │
    ├── scripts/                       # Utility scripts
    │   ├── init_db.py
    │   ├── seed_data.py
    │   ├── run_ingestion.py
    │   └── deploy.sh
    │
    ├── requirements.txt
    ├── Dockerfile
    ├── .env.example
    └── pyproject.toml
```