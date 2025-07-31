# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AURA NEXUS is an advanced lead enrichment system built in Python that consolidates data from multiple sources (Google Maps, web scraping, social media) using multi-LLM consensus for data validation.

## Plan & Review


## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the System
```bash
# Process leads from Excel file
python scripts/process_leads.py --input leads.xlsx

# Run with specific mode
python scripts/process_leads.py --input leads.xlsx --mode basic
python scripts/process_leads.py --input leads.xlsx --mode full_strategy
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_lead_processor.py

# Run with coverage
pytest --cov=src
```

### Code Quality
```bash
# Format code with Black
black src/ tests/

# Check linting with Flake8
flake8 src/ tests/
```

## Architecture

### Core Components

1. **Orchestrator** (`src/core/orchestrator.py`): Main entry point that coordinates all processing. Handles batch processing, checkpointing, and performance monitoring.

2. **Lead Processor** (`src/core/lead_processor.py`): Processes individual leads through various enrichment features based on configured mode.

3. **Multi-LLM Consensus** (`src/core/multi_llm_consensus.py`): Validates and consolidates data using multiple LLMs (GPT, Claude, Gemini) for accuracy.

4. **API Manager** (`src/core/api_manager.py`): Manages API keys and rate limiting for external services.

### Processing Modes

- **basic**: Google Maps, web scraping, social media scraping, contact extraction
- **full_strategy**: All basic features + reviews analysis, competitor analysis, AI insights
- **premium**: All features + facade analysis (Google Street View)

### Data Flow

1. Excel input → SpreadsheetAdapter standardizes format
2. Orchestrator creates batches and manages processing
3. LeadProcessor enriches each lead through configured features
4. Multi-LLM validates critical data points
5. Results saved to timestamped Excel with quality reports

### Key Design Patterns

- **Modular Features**: Each enrichment feature is independent and can be enabled/disabled
- **Async Processing**: Uses asyncio for concurrent API calls and web scraping
- **Multi-Level Caching**: Memory + disk cache to avoid redundant API calls
- **Checkpoint System**: Saves progress incrementally to handle interruptions
- **Adapter Pattern**: SpreadsheetAdapter handles different Excel formats

## Important Considerations

1. **API Keys Required**: Google Maps, OpenAI/Anthropic/Gemini, Apify for social scraping
2. **Rate Limiting**: System respects API rate limits automatically
3. **Data Validation**: Multi-LLM consensus ensures data quality
4. **Error Handling**: Graceful degradation when features fail
5. **Performance**: Batch processing with configurable concurrency