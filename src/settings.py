"""Configuration for Pocket Portals."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Settings:
    """Application settings."""

    anthropic_api_key: str
    log_level: str = "INFO"
    crew_verbose: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        return cls(
            anthropic_api_key=api_key,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            crew_verbose=os.getenv("CREW_VERBOSE", "true").lower() == "true",
        )


# Global settings instance
settings = Settings.from_env()
