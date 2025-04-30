import os
import logging.config

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database settings
DB_FILE = os.path.join(BASE_DIR, "article_database.json")

# Scan settings
SCAN_INTERVAL = 30  # How often to scan for new articles (in minutes)
ARTICLE_LIMIT_PER_SOURCE = 10  # How many articles to fetch per source per scan

# Analysis settings
SIGNIFICANCE_THRESHOLD = 0.6  # Threshold for considering an article significant based on traditional analysis
REQUIRE_SELL_SIGNAL = False  # Whether to require a sell signal for traditional opportunity detection
USE_AI_ANALYSIS = True  # Whether to use AI analysis for opportunity detection
USE_TRADITIONAL_ANALYSIS = False  # Whether to use traditional analysis for opportunity detection (based on keywords)
AI_SIGNIFICANCE_THRESHOLD = 0.7  # Threshold for AI significance score

# OpenAI settings (these can be overridden by environment variables)
# To use OpenAI, set environment variables:
#   OPENAI_API_KEY=your-api-key
#   USE_REAL_AI=true

# Source settings
ACTIVE_SOURCES = ["Bitcoinist", "Cointelegraph", "CryptoPanic", "Reddit Bitcoin", "Google Search", "Bitcoin Magazine", "Bitcoin News RSS", "TradingView"]  # Sources to scan (can be expanded later)

# Email notification settings
EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'  # Whether to send email notifications
EMAIL_FREQUENCY = os.environ.get('EMAIL_FREQUENCY', 'instant')  # Options: 'instant', 'hourly', 'daily'
EMAIL_SMTP_SERVER = os.environ.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com')  # SMTP server
EMAIL_SMTP_PORT = int(os.environ.get('EMAIL_SMTP_PORT', '587'))  # SMTP port

# Output settings
SIMPLIFIED_OUTPUT = os.environ.get('SIMPLIFIED_OUTPUT', 'false').lower() == 'true'

# Configure logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'filename': os.path.join(BASE_DIR, 'bitcoin_news_scanner.log'),
            'mode': 'a',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

# Initialize logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
