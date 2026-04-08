from langchain_openai import ChatOpenAI

from judge.settings import settings


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.zai_base_url,
        api_key=settings.zai_api_key,
        model=settings.zai_model,
        temperature=0,
        max_retries=5,
    )
