from dataclasses import dataclass


def _positive_int(env, name, default):
    value = env.int(name, default=default)
    if value <= 0:
        raise ValueError(f'{name} debe ser un entero mayor que cero.')
    return value


@dataclass(frozen=True)
class AISettings:
    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_primary_model: str
    openrouter_fallback_models: tuple[str, ...]
    allow_paid_models: bool
    max_daily_llm_requests: int
    max_input_tokens: int
    max_output_tokens: int
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    rag_chunk_size: int
    rag_chunk_overlap: int
    rag_top_k: int


def load_ai_settings(env):
    chunk_size = _positive_int(env, 'RAG_CHUNK_SIZE', 600)
    chunk_overlap = env.int('RAG_CHUNK_OVERLAP', default=80)
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            'RAG_CHUNK_OVERLAP debe ser mayor o igual a cero y menor que '
            'RAG_CHUNK_SIZE.'
        )
    return AISettings(
        openrouter_api_key=env.str('OPENROUTER_API_KEY', default=''),
        openrouter_base_url=env.str(
            'OPENROUTER_BASE_URL', default='https://openrouter.ai/api/v1'
        ).rstrip('/'),
        openrouter_primary_model=env.str(
            'OPENROUTER_PRIMARY_MODEL', default='openrouter/free'
        ),
        openrouter_fallback_models=tuple(env.list(
            'OPENROUTER_FALLBACK_MODELS', default=[]
        )),
        allow_paid_models=env.bool('ALLOW_PAID_MODELS', default=False),
        max_daily_llm_requests=_positive_int(env, 'MAX_DAILY_LLM_REQUESTS', 50),
        max_input_tokens=_positive_int(env, 'MAX_INPUT_TOKENS', 8000),
        max_output_tokens=_positive_int(env, 'MAX_OUTPUT_TOKENS', 1500),
        embedding_provider=env.str('EMBEDDING_PROVIDER', default='local'),
        embedding_model=env.str('EMBEDDING_MODEL', default='BAAI/bge-m3'),
        embedding_dimension=_positive_int(env, 'EMBEDDING_DIMENSION', 1024),
        rag_chunk_size=chunk_size,
        rag_chunk_overlap=chunk_overlap,
        rag_top_k=_positive_int(env, 'RAG_TOP_K', 8),
    )
