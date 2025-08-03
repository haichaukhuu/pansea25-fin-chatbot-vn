```
vietnamese-farmer-finance-chatbot/
├── README.md
├── docker-compose.yml
├── .env.example
├── requirements.txt
│
├── frontend/                          # React.js Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── VoiceInput.tsx
│   │   │   └── FinancialDashboard.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── auth.ts
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
│
├── backend/                           # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── config.py                  # Configuration management
│   │   │
│   │   ├── agents/                    # Multi-Agent System
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # Abstract base agent
│   │   │   ├── orchestrator.py        # Main orchestrator
│   │   │   ├── financial_agent.py     # Financial advice agent
│   │   │   ├── rag_agent.py           # RAG retrieval agent
│   │   │   ├── search_agent.py        # Web search agent
│   │   │   └── context_manager.py     # Chat history manager
│   │   │
│   │   ├── models/                    # AI Model Integrations
│   │   │   ├── __init__.py
│   │   │   ├── base_model.py          # Abstract model interface
│   │   │   ├── sea_lion_model.py      # SEA-LION integration
│   │   │   ├── embedding_model.py     # Embedding model wrapper
│   │   │   ├── speech_model.py        # VinAI STT/TTS integration
│   │   │   └── model_factory.py       # Model selection logic
│   │   │
│   │   ├── services/                  # Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── chat_service.py        # Main chat orchestration
│   │   │   ├── rag_service.py         # RAG pipeline
│   │   │   ├── search_service.py      # Web search service
│   │   │   ├── financial_service.py   # Financial data processing
│   │   │   └── auth_service.py        # Authentication logic
│   │   │
│   │   ├── database/                  # Database Layer
│   │   │   ├── __init__.py
│   │   │   ├── postgres_client.py     # PostgreSQL operations
│   │   │   ├── qdrant_client.py       # Vector database client
│   │   │   ├── elasticsearch_client.py # Search index client
│   │   │   └── models.py              # SQLAlchemy models
│   │   │
│   │   ├── api/                       # API Routes
│   │   │   ├── __init__.py
│   │   │   ├── chat.py                # Chat endpoints
│   │   │   ├── auth.py                # Authentication endpoints
│   │   │   ├── financial.py           # Financial data endpoints
│   │   │   └── speech.py              # Speech processing endpoints
│   │   │
│   │   └── utils/                     # Utilities
│   │       ├── __init__.py
│   │       ├── vietnamese_processor.py # Vietnamese text processing
│   │       ├── validators.py          # Data validation
│   │       ├── logger.py              # Logging configuration
│   │       └── exceptions.py          # Custom exceptions
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/                         # Unit & Integration Tests
│       ├── test_agents/
│       ├── test_models/
│       ├── test_services/
│       └── conftest.py
│
├── data-pipeline/                     # Data Engineering
│   ├── scrapers/                      # Web Scraping
│   │   ├── __init__.py
│   │   ├── bank_scraper.py            # Bank data scraper
│   │   ├── government_scraper.py      # Government policy scraper
│   │   ├── news_scraper.py            # Financial news scraper
│   │   └── base_scraper.py            # Abstract scraper base
│   │
│   ├── processors/                    # Data Processing
│   │   ├── __init__.py
│   │   ├── kafka_consumer.py          # Kafka message processing
│   │   ├── data_cleaner.py            # Data cleaning & validation
│   │   ├── embedding_processor.py     # Vector embedding generation
│   │   └── indexer.py                 # Database indexing
│   │
│   ├── schedulers/                    # Scheduled Jobs
│   │   ├── __init__.py
│   │   ├── data_update_scheduler.py   # Automated data updates
│   │   └── maintenance_scheduler.py   # Database maintenance
│   │
│   └── config/
│       ├── kafka_config.py            # Kafka configuration
│       ├── scraper_config.py          # Scraper settings
│       └── database_config.py         # Database settings
│
├── infrastructure/                    # Infrastructure as Code
│   ├── docker/
│   │   ├── kafka/
│   │   ├── qdrant/
│   │   ├── elasticsearch/
│   │   └── postgres/
│   │
│   ├── gcp/                          # Google Cloud deployment
│   │   ├── cloud-run/
│   │   ├── vertex-ai/
│   │   └── firebase/
│   │
│   └── monitoring/                   # Monitoring & Logging
│       ├── prometheus/
│       ├── grafana/
│       └── alerting/
│
├── docs/                             # Documentation
│   ├── API.md                        # API documentation
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── DATA_PIPELINE.md              # Data engineering docs
│   └── AGENTS.md                     # Agent architecture docs
│
└── scripts/                          # Utility Scripts
    ├── setup.sh                      # Environment setup
    ├── deploy.sh                     # Deployment script
    ├── data_migration.py             # Database migration
    └── test_deployment.py            # Deployment testing
```