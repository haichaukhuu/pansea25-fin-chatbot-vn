# AgriFinHub Backend Directory Structure

```
backend/
├──  api/                          # API Gateway Layer
│   ├──  routes/                   # Route handlers
│   │   ├── auth.py                  # Authentication routes
│   │   ├── chat.py                  # Chat orchestration routes
│   │   ├── recommendations.py       # Recommendation engine routes
│   │   ├── rag.py                   # RAG workflow routes
│   │   └── users.py                 # User management routes
│   ├──  middleware/               # Custom middleware
│   │   ├── cors.py                  # CORS configuration
│   │   ├── auth_middleware.py       # JWT validation
│   │   └── rate_limiting.py         # Rate limiting
│   └── gateway.py                   # Main API gateway entry point
│
├──  core/                         # Core App Module
│   ├──  services/                 # Business logic services
│   │   ├── user_service.py          # User management logic
│   │   ├── chat_service.py          # Chat orchestration logic
│   │   ├── recommendation_service.py # Financial recommendations
│   │   └── rag_service.py           # RAG workflow logic
│   ├──  models/                   # Data models & schemas
│   │   ├── user.py                  # User data models
│   │   ├── chat.py                  # Chat message models
│   │   ├── financial.py             # Financial program models
│   │   └── document.py              # Document models
│   └── __init__.py
│
├──  external_services/            # Separate Specialized Services
│   ├──  web_crawler/              # Web scraping service
│   │   ├── crawler.py               # Main crawler logic
│   │   ├── scrapers/                # Specific scrapers
│   │   │   ├── gov_portal.py        # Government portal scraper
│   │   │   ├── bank_websites.py     # Bank website scraper
│   │   │   └── news_scraper.py      # Financial news scraper
│   │   └── __init__.py
│   ├──  search/                   # Web search service
│   │   ├── search_engine.py         # Search implementation
│   │   └── __init__.py
│   ├──  translation/              # Translation service
│   │   ├── translator.py            # Vietnamese translation
│   │   └── __init__.py
│   └──  speech/                   # Speech-to-text service
│       ├── speech_processor.py      # Audio processing
│       └── __init__.py
│
├──  database/                     # Data Storage Layer
│   ├──  connections/              # Database connections
│   │   ├── rds_postgres.py              # PostgreSQL connection
│   │   ├── s3.py                    # S3 storage connection
│   │   ├── vector_db.py             # Vector database connection
│   │   └── neo4j.py                 # Neo4j connection (optional)
│   └──  repositories/             # Data access layer
│       ├── user_repository.py       # User data operations
│       ├── document_repository.py   # Document operations
│       ├── vector_repository.py     # Vector operations
│       └── chat_repository.py       # Chat history operations
│
├──  ai_models/                    # AI Models Integration
│   ├── llm_client.py                # LLM API client (OpenAI/Claude)
│   ├── embeddings.py                # Text embedding service
│   ├── vector_search.py             # Vector similarity search
│   └── __init__.py
│
├──  utils/                        # Utility functions
│   ├── logger.py                    # Logging configuration
│   ├── validators.py                # Input validation
│   ├── helpers.py                   # Common helper functions
│   ├── constants.py                 # Application constants
│   └── vietnamese_utils.py          # Vietnamese text processing
│
├──  config/                       # Configuration
│   ├── settings.py                  # Main configuration
│   ├── database.py                  # Database configurations
│   └── __init__.py
│
├──  tests/                        # Test files
│   ├── test_api/                    # API tests
│   ├── test_services/               # Service tests
│   └── test_utils/                  # Utility tests
│
├──  docs/                         # Documentation
│   ├── api_docs.md                  # API documentation
│   └── setup_guide.md               # Setup instructions
│
├── __init__.py
├── .gitignore
├── config.py                        # Main config file
├── env.example                      # Environment variables template
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
└── run.py                          # Development server runner
```