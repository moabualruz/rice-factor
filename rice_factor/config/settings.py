"""Rice-Factor configuration management using Dynaconf.

Implements 12-Factor App compliant configuration with layered priority:
1. CLI arguments (highest) - handled by Typer
2. Environment variables (RICE_* prefix)
3. Project config (.rice-factor.yaml)
4. User config (~/.rice-factor/config.yaml)
5. Defaults (lowest)
"""

from pathlib import Path

from dynaconf import Dynaconf

# Determine default config file locations
_user_config_dir = Path.home() / ".rice-factor"
_user_config_file = _user_config_dir / "config.yaml"
_project_config_file = Path(".rice-factor.yaml")
_defaults_file = Path(__file__).parent / "defaults.yaml"

# Build settings file list (order matters - later files override earlier)
_settings_files: list[str | Path] = [_defaults_file]

if _user_config_file.exists():
    _settings_files.append(_user_config_file)

if _project_config_file.exists():
    _settings_files.append(_project_config_file)

settings = Dynaconf(
    envvar_prefix="RICE",
    settings_files=_settings_files,
    load_dotenv=True,
    environments=False,  # We don't use Dynaconf environments
    merge_enabled=True,  # Enable deep merge for nested config
)


def reload_settings() -> None:
    """Reload configuration from all sources.

    Call this after modifying config files to pick up changes
    without restarting the application.
    """
    settings.reload()


def get_config_paths() -> dict[str, Path | None]:
    """Return the paths of all config files being used.

    Returns:
        Dictionary with config source names and their paths (or None if not found).
    """
    return {
        "defaults": _defaults_file if _defaults_file.exists() else None,
        "user": _user_config_file if _user_config_file.exists() else None,
        "project": _project_config_file if _project_config_file.exists() else None,
    }


def get_rate_limits_config() -> dict:
    """Load rate limits configuration.

    Returns:
        Dictionary with rate limit configuration, or empty dict if not configured.
    """
    rate_limits_file = Path(__file__).parent / "rate_limits.yaml"
    if not rate_limits_file.exists():
        return {}

    try:
        import yaml

        with rate_limits_file.open() as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return {}


def get_provider_rate_limits(provider: str) -> dict:
    """Get rate limits for a specific provider.

    Args:
        provider: Provider name (claude, openai, etc.).

    Returns:
        Dictionary with provider's rate limits, or defaults if not configured.
    """
    config = get_rate_limits_config()
    providers = config.get("providers", {})

    # Try to get provider-specific config
    if provider in providers:
        return providers[provider]

    # Fall back to defaults
    defaults = config.get("defaults", {})
    return {
        "requests_per_minute": 60,
        "tokens_per_minute": 100000,
        "tokens_per_day": 10000000,
        "concurrent_requests": 10,
        "enabled": defaults.get("enabled", True),
    }


def get_rate_limit_tier(tier: str) -> dict:
    """Get rate limits for a tier preset.

    Args:
        tier: Tier name (free, standard, professional, enterprise, local).

    Returns:
        Dictionary with tier's rate limits, or standard tier if not found.
    """
    config = get_rate_limits_config()
    tiers = config.get("tiers", {})

    if tier in tiers:
        return tiers[tier]

    # Fall back to standard tier
    return tiers.get(
        "standard",
        {
            "requests_per_minute": 60,
            "tokens_per_minute": 100000,
            "tokens_per_day": 5000000,
            "concurrent_requests": 5,
        },
    )
