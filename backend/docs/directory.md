
```
backend/
├──  api/                          # API Gateway Layer
│   ├──  routes/                   # Route handlers
│   │   ├── auth.py                  # Authentication routes
│   │   ├── chat.py                  # Chat orchestration routes
│   │   ├── preferences_route.py     # User preferences routes
│   │   ├── transcription_route.py   # Speech transcription routes
│   │   ├── weather.py               # Weather information routes
│   │   └── web_scraping.py         # Web scraping routes
│   ├──  middleware/               # Custom middleware
│   │   └── auth_middleware.py       # JWT validation
│   └── __init__.py
│
├──  core/                         # Core App Module
│   ├──  models/                   # Data models
│   │   ├── transcription_models.py  # Transcription models
│   │   └── user.py                  # User models
│   ├──  services/                 # Business logic services
│   │   ├── auth_service.py          # Authentication logic
│   │   ├── chat_history_service.py  # Chat history management
│   │   ├── preference_service.py    # User preferences logic
│   │   └── transcription_service.py # Transcription service logic
│   └── __init__.py
│
├──  external_services/            # Separate Specialized Services
│   ├──  weather_service/          # Weather information service
│   │   ├── weather_service.py       # Weather service implementation
│   │   ├── weather_scraper.py       # Weather data scraper
│   │   ├── location_mapper.py       # Location mapping utility
│   │   ├── models.py               # Weather data models
│   │   └── vn_stations.json        # Vietnam weather stations data
│   └──  web_scrap_crawl/         # Web scraping service
│       ├── crawler.py              # Main crawler logic
│       ├── scraper.py             # Web scraping implementation
│       ├── service.py             # Scraping service layer
│       └── models.py              # Scraping data models
│
├──  database/                     # Data Storage Layer
│   ├──  connections/              # Database connections
│   │   ├── dynamodb_chat_history.py # DynamoDB chat history
│   │   ├── dynamodb_preference.py   # DynamoDB preferences
│   │   └── rds_postgres.py         # PostgreSQL connection
│   ├──  models/                   # Data models & schemas
│   │   ├── chat_history_item.py    # Chat history model
│   │   ├── preference_models.py     # Preferences model
│   │   └── user.py                 # User model
│   └──  repositories/             # Data access layer
│       ├── chat_history_repository.py  # Chat history operations
│       ├── preference_repository.py    # Preferences operations
│       └── user_repository.py         # User data operations
│
├──  ai_models/ (legacy)            # AI Models
│   ├── base_model.py               # Base AI model class
│   ├── embedding_model.py          # Embedding model
│   ├── google_genai_model.py       # Google Gemini integration
│   ├── llm_client.py              
│   ├── model_factory.py           
│   └── model_manager.py           
│
├──  agents/ (current)
│   ├── llm_clients.py
│   ├── react_agent.py
│   ├── prompts_config.json #contains k-v pairs to load the corresponding prompt for each llm
│   ├── prompts/
│   ├── tools/
│   │   ├── rag_kb.py
│   │   └── get_weather_info.py
│   └── __init__.py
│
├──  scripts/                      # Utility Scripts
│   ├── clear_all_users_from_rds_db.py
│   ├── create_rds_db.py
│   ├── delete_rds_db.py
│   └── list_rds_db.py
│
├──  tests/                        # Test files
│   ├── test_ai_models/             # AI model tests
│   ├── test_api/                   # API tests
│   ├── test_core/                  # Core module tests
│   └── conftest.py                 # Test configurations
│
├──  docs/                         # Documentation
│   ├── data_sources.json           # Data sources configuration
│   └── directory.md               # Project structure documentation
│
├── __init__.py
├── .gitignore
├── config.py                        # Main config file
├── env.example                      # Environment variables template
├── main.py                         # Application entry point
├── requirements.txt                 # Python dependencies
└── run.py                          # Development server runner
```
