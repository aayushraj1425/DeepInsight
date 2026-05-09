import os
import openai
import instructor

_instance: instructor.Instructor | None = None


def _get() -> instructor.Instructor:
    global _instance
    if _instance is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env")
        _instance = instructor.from_openai(openai.AsyncOpenAI(api_key=key))
    return _instance


class _LazyClient:
    """Proxy that initialises the OpenAI+Instructor client on first attribute access."""
    def __getattr__(self, name: str):
        return getattr(_get(), name)


client = _LazyClient()
