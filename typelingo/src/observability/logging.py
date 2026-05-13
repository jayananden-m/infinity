"""Structured logging configuration using structlog."""

import structlog


def configure_logging(debug: bool = False) -> None:
    """Configure structlog processors.

    In debug mode: pretty console output + DEBUG level.
    In production: JSON output + INFO level.
    """
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    if debug:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(10 if debug else 20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a bound logger for the given module name."""
    logger: structlog.BoundLogger = structlog.get_logger(name)
    return logger
