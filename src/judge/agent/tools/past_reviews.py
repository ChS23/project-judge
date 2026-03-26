from langchain_core.tools import tool

from judge.github.client import get_comments
from judge.models.pr import PRContext


def make_read_past_reviews(pr: PRContext):
    @tool
    async def read_past_reviews() -> str:
        """Прочитать прошлые оценки бота в этом PR.

        Вызывай в начале проверки чтобы узнать:
        - Какие замечания были в прошлый раз
        - Какие баллы были выставлены
        - Что студент должен был исправить

        При перепроверке сравни текущее состояние с прошлыми замечаниями \
        и отметь что исправлено, а что нет.
        """
        comments = await get_comments(pr)

        reviews = []
        for c in comments:
            if c["user"].endswith("[bot]") and "Результат" in c["body"]:
                reviews.append(
                    f"--- Оценка от {c['created_at']} ---\n{c['body'][:3000]}"
                )

        if not reviews:
            return "Прошлых оценок нет — это первая проверка."

        return f"Найдено {len(reviews)} прошлых оценок:\n\n" + "\n\n".join(reviews)

    return read_past_reviews
