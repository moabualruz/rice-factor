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
