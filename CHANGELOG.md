# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2025-12-21

### Added
- Interactive narrative API with CrewAI agent orchestration
- Multi-agent system with Dungeon Master, Narrator, and Lore Keeper roles
- Session management for multi-user support with UUID-based tracking
- Choice system with 3 pre-generated options plus free text input
- Conversation context passing to maintain narrative continuity
- Retro RPG web UI with static file serving
- Starter choices with randomized shuffling for variety
- Docker containerization for development and deployment environments
- Comprehensive onboarding guide with mermaid diagrams
- Insomnia API collection for testing endpoints
- TDD/BDD practices guide for developers
- Example scripts demonstrating agent voice refinement
- Agentic development framework with YAML-based agent configuration
- CrewAI integration with FastAPI backend
- Product requirements document (PRD)

### Changed
- Improved UI readability with enhanced typography and spacing
- Improved narrative output formatting for better readability
- Updated README with detailed project overview and API examples
- Enhanced ONBOARDING.md for better agent/developer success
- Refined agent voices and personalities through example scripts

### Fixed
- Static file mounting to use `/static` path instead of overriding API routes
- Path obfuscation in documentation for security
- Render deployment configuration: standard pip install (Python 3.12)
