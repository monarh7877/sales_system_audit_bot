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
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==== НАСТРОЙКИ ====
# Токен берётся из переменной окружения BOT_TOKEN (задаётся в Railway в разделе Variables).
# Для локального теста можно временно вписать токен прямо в строку ниже после os.environ.get("BOT_TOKEN", "сюда токен").
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Твой личный chat_id — сюда будут приходить уведомления о новых заявках на курс
# и на разбор воронки.
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "5475589991")

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
        context.user_data["awaiting"] = "call_request"
        await query.message.reply_text(
            "Отлично! Напиши, пожалуйста, в одном сообщении:\n"
            "1) Сферу бизнеса\n"
            "2) Сколько человек в отделе продаж\n"
            "3) Удобное время для звонка\n\n"
            "Отвечу в течение дня и согласуем время."
        )

    elif query.data == "ask_course":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Записаться на курс — 40 000₽", callback_data="apply_course")],
        ])
        await query.message.reply_text(
            "Курс предназначен для собственников и РОПов, которые хотят системно выстроить отдел продаж "
            "и не зависеть от наёмного консультанта в будущем.\n\n"
            "Стоимость: 40 000₽.\n\n"
            "Если готов — нажми кнопку ниже, и я свяжусь с тобой, чтобы согласовать детали и оплату.",
            reply_markup=keyboard,
        )

    elif query.data == "apply_course":
        context.user_data["awaiting"] = "course_request"
        await query.message.reply_text(
            "Супер! Напиши, пожалуйста, в одном сообщении:\n"
            "1) Сферу бизнеса\n"
            "2) Сколько человек в отделе продаж\n"
            "3) Лучший способ связи (телефон или этот Telegram)\n\n"
            "Я свяжусь с тобой в течение дня, чтобы согласовать программу и оплату."
        )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые ответы пользователя на заявки (звонок или курс)."""
    awaiting = context.user_data.get("awaiting")
    if not awaiting:
        return

    user = update.effective_user
    user_label = f"@{user.username}" if user.username else f"{user.first_name} (id {user.id})"

    if awaiting == "call_request":
        notify_text = (
            f"🔔 Новая заявка на разбор воронки!\n\n"
            f"От: {user_label}\n\n"
            f"Сообщение:\n{update.message.text}"
        )
    elif awaiting == "course_request":
        notify_text = (
            f"💰 Новая заявка на курс (40 000₽)!\n\n"
            f"От: {user_label}\n\n"
            f"Сообщение:\n{update.message.text}"
        )
    else:
        return

    # Отправляем уведомление администратору
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=notify_text)
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление администратору: {e}")

    # Подтверждаем пользователю получение заявки
    await update.message.reply_text(
        "Спасибо! Заявку получил, свяжусь с тобой в течение дня. 🙌"
    )

    context.user_data["awaiting"] = None


def main() -> None:
    if not BOT_TOKEN:
        print("ОШИБКА: переменная окружения BOT_TOKEN не задана.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
