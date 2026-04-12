from langchain_openai import ChatOpenAI

from judge.settings import settings


def get_llm() -> ChatOpenAI:
    model = settings.zai_model
    # GLM-5.x с thinking mode требует temperature=1.0
    is_glm5 = model.startswith("glm-5")
    temp = 1.0 if is_glm5 else 0

    return ChatOpenAI(
        base_url=settings.zai_base_url,
        api_key=settings.zai_api_key,
        model=model,
        temperature=temp,
        max_retries=5,
    )
