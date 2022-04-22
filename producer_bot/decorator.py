from functools import wraps
from typing import Callable

from opentelemetry import trace


def start_as_current_span(tracer, span_name: str) -> Callable:
    def decorator(func: Callable):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                return func(*args, **kwargs, span=span)

        return func_wrapper

    return decorator
