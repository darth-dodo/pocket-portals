# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **CharacterBuilderAgent**: LLM-powered intelligent stat generation from interview conversations
  - Uses CrewAI's `output_pydantic` pattern for structured JSON output
  - Analyzes 5-turn interview to determine appropriate race, class, and stats
  - Stat generation follows D&D rules: total 70-80 points, primary stat 14-16
  - Fallback mechanism for LLM failures with default human fighter
- **Character Sheet API Integration**: Frontend receives character data after creation
  - `CharacterSheetData` Pydantic model for API responses
  - SSE `game_state` event emits character sheet after turn 5
  - Both `/start?skip_creation=true` and typing "skip" return character_sheet
- **Character Sheet E2E Tests**: Playwright tests 11-14 for character sheet UI
  - Display test: stats, HP bar, quest section
  - Collapse/expand test: toggle functionality
  - Theme integration: all 4 themes properly style character sheet
  - Mobile responsive: 2-column grid, touch-friendly collapse
- **Comprehensive JavaScript Test Suite**: 415 tests with 96.49% statement coverage
  - Vitest with jsdom environment for DOM testing
  - Test files for: api, combat, controllers, game-state, haptics, main, messages, themes
  - CI/CD integration with coverage reporting
- **Haptic Feedback System**: Mobile vibration for enhanced interaction (`static/js/haptics.js`)
  - Vibration API integration with graceful fallback
  - Tactile feedback patterns: light, medium, success, error, combat
  - Feature detection for unsupported browsers
- **Theme System**: 5 visual themes with localStorage persistence (`static/js/themes.js`)
  - Themes: Dark (default), Light, Dungeon, Forest, Celestial
  - CSS custom properties for dynamic theming
  - Theme selector in settings modal
- **iOS Safe Area Support**: Proper handling of iPhone notch and home indicator
  - CSS env() functions for safe-area-inset values
  - Consistent padding across all iOS devices
- **Adventure Pacing System**: 50-turn adventure structure with 5-phase narrative arc
  - AdventurePhase enum: SETUP, RISING_ACTION, MID_POINT, CLIMAX, DENOUEMENT
  - Turn tracking with automatic phase progression
  - PacingContext model for agent narrative guidance
  - Closure triggers: quest completion (after turn 25) or hard cap (turn 50)
- **EpilogueAgent**: Personalized adventure conclusions
  - References specific adventure moments
  - Character-aware epilogue generation
  - Graceful fallback for LLM failures
- **Pacing Guidelines**: Narrator receives phase-specific storytelling guidance
- **Adventure Moments**: Tracking system for significant story events
- New ADR: `docs/adr/003-adventure-pacing-system.md`
- New design doc: `docs/design/2025-12-29-adventure-pacing-system.md`

### Changed
- **Modern Button System**: Replaced NES.css with custom CSS button styling
  - Custom CSS variables for consistent theming
  - Flexbox-based layout for responsive design
- **Improved Touch Targets**: Minimum 48px touch targets for WCAG 2.1 AAA compliance
- **Theme Modal Scrollability**: Fixed modal cut-off on mobile with max-height and overflow
- GameState model extended with adventure_turn, adventure_phase, max_turns fields
- SessionManager with turn increment and epilogue trigger methods
- API process_action() integrates pacing context and closure detection
- Agent configuration updated with pacing guidelines

### Removed
- **NES.css Dependency**: Replaced with modern, custom CSS button system
- **Keyboard Shortcuts**: Simplified interaction model for mobile-first approach

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
