"""
AI Prozorro Intelligence - Groq AI клієнт.
Генерує пояснення на основі оцінки ризику.
"""

import asyncio
import logging
import threading
import time
from collections import deque
from datetime import date
from typing import Optional

from groq import Groq, AsyncGroq

from app.core.config import settings

logger = logging.getLogger(__name__)

# Обов'язкове застереження - додається програмно до кожного аналізу,
# щоб гарантувати точний текст та зекономити токени генерації
DISCLAIMER = (
    "\n\n⚠️ Цей аналітичний коментар сформовано автоматизованою моделлю на основі "
    "відкритих даних Prozorro. Він є попередньою аналітичною оцінкою і НЕ є "
    "висновком про порушення законодавства, доказом чи звинуваченням. Висновки "
    "можуть бути помилковими або неповними через обмеженість даних. Остаточну "
    "оцінку відповідності закупівлі вимогам законодавства може надати лише "
    "уповноважений державний орган (АМКУ, ДАСУ) за результатами офіційної перевірки."
)


class GroqRateLimiter:
    """
    Обмежувач запитів під ліміти Groq (безкоштовний тариф):
    - 30 запитів за хвилину (тримаємо 28 із запасом на ретраї SDK)
    - 1000 запитів за день (тримаємо 950 із запасом)
    Потокобезпечний: працює і з планувальником, і з admin-endpoint.
    """

    def __init__(self, max_per_minute: int, max_per_day: int):
        self.max_per_minute = max_per_minute
        self.max_per_day = max_per_day
        self._timestamps: deque = deque()  # моменти запитів за останні 60 сек
        self._day = date.today()
        self._daily_count = 0
        self._lock = threading.Lock()

    def _seconds_to_wait(self) -> float:
        """Скільки чекати до наступного дозволеного запиту (0 = можна одразу)."""
        now = time.monotonic()
        while self._timestamps and now - self._timestamps[0] > 60:
            self._timestamps.popleft()
        if len(self._timestamps) < self.max_per_minute:
            return 0.0
        return 60.0 - (now - self._timestamps[0]) + 0.2

    async def acquire(self) -> bool:
        """
        Дочекатися дозволу на запит.
        Повертає False, якщо денний ліміт вичерпано (запит робити не можна).
        """
        while True:
            with self._lock:
                # Скидання денного лічильника опівночі
                today = date.today()
                if today != self._day:
                    self._day = today
                    self._daily_count = 0

                if self._daily_count >= self.max_per_day:
                    logger.warning(
                        f"Groq: денний ліміт {self.max_per_day} запитів вичерпано, "
                        f"AI аналіз відкладено до завтра"
                    )
                    return False

                wait = self._seconds_to_wait()
                if wait <= 0:
                    self._timestamps.append(time.monotonic())
                    self._daily_count += 1
                    return True

            # Чекаємо поза локом, щоб не блокувати інші задачі
            logger.debug(f"Groq rate limit: пауза {wait:.1f} сек (ліміт {self.max_per_minute}/хв)")
            await asyncio.sleep(wait)

    @property
    def daily_remaining(self) -> int:
        with self._lock:
            if date.today() != self._day:
                return self.max_per_day
            return max(0, self.max_per_day - self._daily_count)


rate_limiter = GroqRateLimiter(
    max_per_minute=settings.groq_max_requests_per_minute,
    max_per_day=settings.groq_max_requests_per_day,
)


def get_groq_client() -> Optional[AsyncGroq]:
    """Отримати клієнт Groq (якщо API ключ налаштований)."""
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY не налаштований, AI аналіз вимкнений")
        return None
    # max_retries=1: ретраї SDK теж рахуються у ліміт 30 запитів/хв
    return AsyncGroq(api_key=settings.groq_api_key, max_retries=1)


async def generate_ai_explanation(
    tender_title: str,
    tender_amount: float,
    risk_score: int,
    risk_factors: list,
    currency: str = "UAH",
    region: Optional[str] = None,
    status: Optional[str] = None,
    participants_count: int = 0,
    buyer_name: Optional[str] = None,
    winner_name: Optional[str] = None,
    cpv_code: Optional[str] = None,
    prozorro_id: Optional[str] = None,
    published_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category_avg: Optional[float] = None,
    category_count: int = 0,
    price_examples: Optional[list] = None,
) -> Optional[str]:
    """
    Згенерувати структурований аналітичний AI-коментар щодо ризиків тендера через Groq.

    Returns:
        Текстовий аналіз за 9 критеріями + фінальна оцінка + застереження, або None
    """
    client = get_groq_client()
    if not client:
        return None

    # Спрацьовані фактори Risk Engine
    factors_text = "\n".join([
        f"- {f.get('description_uk', f.get('key'))} (+{f.get('weight')} балів)"
        for f in risk_factors
    ]) or "Жодних факторів ризику не виявлено."

    # Дані тендеру (лише наявні поля)
    data_lines = []
    if prozorro_id:
        data_lines.append(f"Номер тендеру: {prozorro_id}")
    data_lines.append(f"Предмет закупівлі: {tender_title}")
    data_lines.append(f"Очікувана вартість: {tender_amount:,.0f} {currency}")
    if buyer_name:
        data_lines.append(f"Замовник: {buyer_name}")
    if winner_name:
        data_lines.append(f"Переможець: {winner_name}")
    data_lines.append(f"Кількість учасників: {participants_count}")
    if region:
        data_lines.append(f"Регіон: {region}")
    if cpv_code:
        data_lines.append(f"Категорія CPV: {cpv_code}")
    if status:
        data_lines.append(f"Статус: {status}")
    if published_date:
        data_lines.append(f"Дата публікації: {published_date}")
    if end_date:
        data_lines.append(f"Кінцевий строк подання: {end_date}")

    # Порівняльні дані цін по категорії (для критерію "Ціна")
    if category_avg and category_count:
        deviation = ((tender_amount - category_avg) / category_avg * 100) if tender_amount else 0
        data_lines.append(
            f"Середня вартість тендерів у категорії {cpv_code}: {category_avg:,.0f} {currency} "
            f"(на основі {category_count} тендерів у базі). "
            f"Відхилення цього тендера від середньої: {deviation:+.0f}%"
        )
    if price_examples:
        examples_str = "\n".join([
            f"  - {title[:80]}: {amount:,.0f} {currency}"
            for title, amount in price_examples
        ])
        data_lines.append(f"Приклади цін інших тендерів цієї ж категорії:\n{examples_str}")

    data_lines.append(f"Оцінка ризику системи (Risk Engine): {risk_score}/100")
    data_lines.append(f"Спрацьовані фактори ризику:\n{factors_text}")
    data_text = "\n".join(data_lines)

    prompt = f"""Ти — аналітик з держзакупівель, який допомагає виявляти потенційні ознаки корупційних ризиків та маніпуляцій у тендерах на платформі Prozorro.

Тобі надано дані про тендер. Проаналізуй їх і оціни рівень ризику за наступними критеріями:

1. Умови участі — чи є ознаки штучно звужених вимог, які підходять лише одному постачальнику (специфічні бренди, надто вузькі параметри, нетипові сертифікати).
2. Строки — чи достатньо часу було дано на подання пропозицій, чи не публікувався тендер у "незручний" час (свята, вихідні).
3. Ціна — чи є суттєве відхилення очікуваної/переможної ціни від ринкової (завищення чи підозріло точний збіг з очікуваною вартістю). Якщо надано середню вартість по категорії та приклади цін інших тендерів — обов'язково порівняй з ними і наведи конкретні цифри у поясненні.
4. Кількість учасників — чи була реальна конкуренція, чи участь брала лише одна компанія або компанії, пов'язані між собою.
5. Історія учасника-переможця — чи є ознаки "тендерної кишені" (постійні перемоги в одного замовника, пов'язані засновники, реєстрація незадовго до тендеру).
6. Скасування/зміни — чи тендер скасовувався і публікувався повторно зі зміненими умовами під конкретного учасника.
7. Оскарження — чи були скарги в АМКУ, і чим вони закінчились.
8. Замовник — чи має він історію повторюваних підозрілих закупівель.
9. Ротація учасників — чи є ознаки, що ті самі 2-3 компанії по черзі виграють у цього замовника (імітація конкуренції зі сталим пулом постачальників).

Для кожного пункту вкажи:
- Рівень ризику (низький / середній / високий / недостатньо даних)
- Коротке пояснення (1-2 речення), чому саме

ВАЖЛИВО: якщо для пункту немає даних у наданій інформації — чесно вкажи "недостатньо даних" і НЕ вигадуй факти. Спирайся лише на надані дані та спрацьовані фактори Risk Engine.

У ФІНАЛІ обов'язково додай:
- Загальний індекс ризику (за шкалою 1–10)
- Список 2–4 головних "червоних прапорців", якщо вони є

Не роби категоричних тверджень на кшталт "це корупція", "це незаконно" чи "тендер підозрілий" — використовуй формулювання "може свідчити про", "викликає питання", "варто перевірити додатково".

Формат відповіді: українською мовою, без markdown-розмітки (без **, ##). Кожен критерій з нового рядка у форматі: "1. Умови участі — [рівень]: пояснення". Не додавай застереження в кінці — воно додається автоматично.

Дані тендеру:
{data_text}"""

    try:
        # Дотримання лімітів Groq: 30 запитів/хв, 1000 запитів/день
        if not await rate_limiter.acquire():
            return None

        response = await client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "Ти — досвідчений аналітик державних закупівель України. Твої аналізи структуровані, об'єктивні, обережні у формулюваннях та спираються лише на надані дані.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.4,
            max_tokens=1000,
        )

        return response.choices[0].message.content.strip() + DISCLAIMER

    except Exception as e:
        logger.error(f"Помилка Groq API: {e}")
        return None
