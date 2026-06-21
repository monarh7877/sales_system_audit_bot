"""
Telegram-бот «Аудит воронки продаж».

Принимает deep-link вида:
  https://t.me/<имя_бота>?start=zona-red_pct-42

И отвечает персонализированным сообщением в зависимости от зоны риска.

Установка:
  pip install python-telegram-bot --break-system-packages

Запуск:
  python bot.py

Перед запуском вставь свой токен в переменную BOT_TOKEN ниже
(получить токен у @BotFather в Telegram).
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==== НАСТРОЙКИ ====
# Токен берётся из переменной окружения BOT_TOKEN (задаётся в Railway в разделе Variables).
# Для локального теста можно временно вписать токен прямо в строку ниже после os.environ.get("BOT_TOKEN", "сюда токен").
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Тексты для каждой зоны риска
ZONE_MESSAGES = {
    "red": {
        "title": "🔴 Зона риска",
        "text": (
            "Твой результат показывает, что бизнес сейчас теряет значительную часть потенциальной прибыли.\n\n"
            "Это нормально — почти всегда дело не в людях, а в дырах системы, которые не видны изнутри.\n\n"
            "Я могу разобрать твою воронку подробно и показать, с чего начать, чтобы закрыть самые денежные дыры первыми."
        ),
    },
    "amber": {
        "title": "🟡 Зона роста",
        "text": (
            "Система у тебя частично работает — это хорошая новость, основа есть.\n\n"
            "Но конкретные дыры тормозят рост выручки. Обычно на этом этапе разбор воронки даёт быстрый и заметный эффект.\n\n"
            "Готов показать, на что обратить внимание первым делом."
        ),
    },
    "green": {
        "title": "🟢 Зона устойчивости",
        "text": (
            "Сильный результат — основа крепкая.\n\n"
            "На этом уровне работа идёт уже не про «тушить пожар», а про тонкую настройку и масштабирование того, что уже работает.\n\n"
            "Если интересно — могу показать, где именно можно дотянуть систему до максимума."
        ),
    },
}

DEFAULT_MESSAGE = (
    "Привет! Я помогу разобраться, где твой бизнес теряет деньги в продажах.\n\n"
    "Если ты ещё не проходил диагностику — пройди её по ссылке, а потом возвращайся сюда."
)


def parse_start_param(param: str) -> dict:
    """
    Разбирает строку вида 'zona-red_pct-42' в словарь {'zona': 'red', 'pct': '42'}.
    Использует дефисы и подчёркивания, потому что Telegram deep-link
    поддерживает только [A-Za-z0-9_-] в параметре start.
    """
    result = {}
    if not param:
        return result
    pairs = param.split("_")
    for pair in pairs:
        if "-" in pair:
            key, _, value = pair.partition("-")
            result[key] = value
    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args  # это то, что приходит после /start
    param = args[0] if args else ""
    data = parse_start_param(param)
    zona = data.get("zona")
    pct = data.get("pct")

    if zona in ZONE_MESSAGES:
        info = ZONE_MESSAGES[zona]
        pct_line = f"Твой результат: {pct}%\n\n" if pct else ""
        text = f"{info['title']}\n\n{pct_line}{info['text']}"
    else:
        text = DEFAULT_MESSAGE

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Записаться на разбор воронки", callback_data="book_call")],
        [InlineKeyboardButton("Узнать про курс за 40 000₽", callback_data="ask_course")],
    ])

    await update.message.reply_text(text, reply_markup=keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "book_call":
        await query.message.reply_text(
            "Отлично! Напиши, пожалуйста:\n"
            "1) Сферу бизнеса\n"
            "2) Сколько человек в отделе продаж\n"
            "3) Удобное время для звонка\n\n"
            "Отвечу в течение дня и согласуем время."
        )
    elif query.data == "ask_course":
        await query.message.reply_text(
            "Курс предназначен для собственников и РОПов, которые хотят системно выстроить отдел продаж "
            "и не зависеть от наёмного консультанта в будущем.\n\n"
            "Стоимость: 40 000₽.\n\n"
            "Расскажи коротко о своём бизнесе — пришлю подробную программу."
        )


def main() -> None:
    if not BOT_TOKEN:
        print("ОШИБКА: переменная окружения BOT_TOKEN не задана.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
