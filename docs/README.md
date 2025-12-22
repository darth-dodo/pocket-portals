# Pocket Portals Documentation

Welcome to the Pocket Portals documentation. This directory contains all project documentation organized by purpose.

## Table of Contents

- [Quick Links](#quick-links)
- [Documentation Structure](#documentation-structure)
- [Getting Started](#getting-started)
- [Document Index](#document-index)

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [Crash Course](guides/CRASH-COURSE.md) | Start here - comprehensive spike overview |
| [Onboarding Guide](guides/ONBOARDING.md) | Developer setup and workflow |
| [Product Requirements](product.md) | Features and specifications |
| [Architecture](reference/architecture.md) | Technical design and patterns |

---

## Documentation Structure

```
docs/
├── README.md              # This file - documentation index
├── product.md             # Product requirements document (PRD)
│
├── guides/                # Getting started & tutorials
│   ├── CRASH-COURSE.md    # Comprehensive spike documentation
│   └── ONBOARDING.md      # Developer onboarding guide
│
├── reference/             # Technical reference documentation
│   ├── architecture.md    # System architecture & XP practices
│   ├── conversation-engine.md  # Turn-taking & state management
│   ├── creative-writing.md     # Agent voices & narrative style
│   ├── crewai.md          # CrewAI patterns & templates
│   └── xp.md              # XP methodology guidelines
│
├── design/                # Design specifications
│   ├── design.md          # UI design system
│   ├── choice-system.md   # Choice mechanics design
│   ├── conversation-context.md  # Context management
│   └── starter-choices.md # Adventure hooks design
│
├── adr/                   # Architecture Decision Records
│   └── 001-agent-service-pattern.md
│
└── api/                   # API documentation
    └── insomnia-collection.json  # API testing collection
```

---

## Getting Started

### For New Developers

1. **Read the [Crash Course](guides/CRASH-COURSE.md)** - Get a comprehensive overview of the spike implementation
2. **Follow the [Onboarding Guide](guides/ONBOARDING.md)** - Set up your development environment
3. **Review [Product Requirements](product.md)** - Understand what we're building

### For Understanding the Code

1. **[Architecture](reference/architecture.md)** - System design and patterns
2. **[CrewAI Guide](reference/crewai.md)** - Agent framework usage
3. **[Conversation Engine](reference/conversation-engine.md)** - How turns work

### For UI/UX Work

1. **[Design System](design/design.md)** - Colors, typography, components
2. **[Choice System](design/choice-system.md)** - How choices work

---

## Document Index

### Guides

| Document | Description |
|----------|-------------|
| [Crash Course](guides/CRASH-COURSE.md) | Complete spike documentation with 15 sections covering architecture, patterns, and lessons learned |
| [Onboarding Guide](guides/ONBOARDING.md) | Step-by-step developer setup, workflow instructions, and troubleshooting |

### Reference

| Document | Description |
|----------|-------------|
| [Architecture](reference/architecture.md) | Technical architecture, XP practices, BDD specifications |
| [Conversation Engine](reference/conversation-engine.md) | Turn-taking mechanics, state management, context handling |
| [Creative Writing](reference/creative-writing.md) | Agent personalities, narrative guidelines, voice patterns |
| [CrewAI Guide](reference/crewai.md) | CrewAI patterns, agent configuration, task definitions |
| [XP Methodology](reference/xp.md) | Extreme Programming practices and guidelines |

### Design

| Document | Description |
|----------|-------------|
| [Design System](design/design.md) | UI design system - colors, typography, spacing, components |
| [Choice System](design/choice-system.md) | Choice mechanics - 3 options + free text implementation |
| [Conversation Context](design/conversation-context.md) | Context passing and history management |
| [Starter Choices](design/starter-choices.md) | Adventure hooks and shuffle feature |

### ADRs

| ADR | Decision |
|-----|----------|
| [001](adr/001-agent-service-pattern.md) | Agent service pattern with global singleton |

---

## Contributing to Documentation

When adding new documentation:

1. Place it in the appropriate folder based on purpose
2. Add a table of contents at the top of longer documents
3. Update this README.md to include the new document
4. Use consistent formatting (see existing docs for patterns)
5. Include cross-references to related documents

---

*Last updated: December 2025*
