"""Application configuration.

Values are read from environment variables. Development defaults let the app run
out of the box, but ``validate_config()`` fails fast if the app is started in
production with insecure defaults (weak secret, demo accounts enabled).
"""
import os

# --- Environment ----------------------------------------------------------
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION: bool = ENVIRONMENT == "production"

# --- Database -------------------------------------------------------------
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/appointments",
)

# --- Auth / JWT -----------------------------------------------------------
_INSECURE_SECRET = "dev-secret-change-me"
SECRET_KEY: str = os.getenv("SECRET_KEY", _INSECURE_SECRET)
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# --- CORS -----------------------------------------------------------------
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080",
    ).split(",")
    if origin.strip()
]


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


# --- Seeding --------------------------------------------------------------
# The built-in demo accounts (admin/alice/bob) are convenient for local dev but
# must never be created in production. Off by default in production.
SEED_DEMO_USERS: bool = _as_bool(
    os.getenv("SEED_DEMO_USERS", "false" if IS_PRODUCTION else "true")
)

# Optional first-admin bootstrap for production: if both are set, an admin with
# these credentials is created on startup (if it doesn't already exist).
ADMIN_USERNAME: str | None = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD: str | None = os.getenv("ADMIN_PASSWORD")


def validate_config() -> None:
    """Refuse to start with an insecure configuration in production."""
    if not IS_PRODUCTION:
        return
    problems: list[str] = []
    if SECRET_KEY == _INSECURE_SECRET or len(SECRET_KEY) < 16:
        problems.append("SECRET_KEY must be a strong, non-default value (>= 16 chars)")
    if SEED_DEMO_USERS:
        problems.append("SEED_DEMO_USERS must be disabled in production")
    if any("localhost" in o or "127.0.0.1" in o for o in CORS_ORIGINS):
        problems.append("CORS_ORIGINS should not include localhost in production")
    if problems:
        raise RuntimeError(
            "Insecure production configuration: " + "; ".join(problems)
        )
