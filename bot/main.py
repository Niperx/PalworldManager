"""
Основной файл Telegram бота для управления сервером Palworld
"""
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from palworld_api import PalworldAPI
from config import settings

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация API клиента
palworld_api = PalworldAPI(
    server_url=settings.palworld_server_url,
    admin_password=settings.palworld_admin_password
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    # Проверяем, является ли пользователь администратором
    user = update.effective_user
    admin_usernames = settings.get_admin_usernames()
    is_admin = user and user.username and user.username.lower() in admin_usernames
    
    # Формируем URL для Mini App (Telegram требует HTTPS)
    # Преобразуем HTTP в HTTPS, если нужно
    web_app_url = settings.web_server_url
    if web_app_url.startswith('http://'):
        web_app_url = web_app_url.replace('http://', 'https://', 1)
    
    # Добавляем параметр admin для администратора
    if is_admin:
        separator = '&' if '?' in web_app_url else '?'
        web_app_url = f"{web_app_url}{separator}admin=true"
    
    keyboard = [
        [InlineKeyboardButton("📱 Открыть Mini App", web_app=WebAppInfo(url=web_app_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🎮 Добро пожаловать в бот управления сервером Palworld!\n\n"
        "📱 Mini App позволяет:\n"
        "• Проверить онлайн сервера\n"
        "• Просмотреть карту с игроками\n"
        "• Узнать статус и статистику сервера"
    )
    
    if is_admin:
        welcome_text += "\n\n🔐 Вы вошли как администратор"
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )


async def server_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить информацию о сервере"""
    try:
        info = await palworld_api.get_server_info()
        metrics = await palworld_api.get_metrics()
        
        message = (
            "📊 **Информация о сервере**\n\n"
            f"**Название:** {info.get('name', 'N/A')}\n"
            f"**Версия:** {info.get('version', 'N/A')}\n"
            f"**Описание:** {info.get('description', 'N/A')}\n\n"
            f"**Метрики:**\n"
            f"• Uptime: {metrics.get('uptime', 'N/A')} секунд\n"
            f"• FPS: {metrics.get('fps', 'N/A')}\n"
            f"• Игроков онлайн: {len(await palworld_api.get_players())}\n"
        )
        
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка при получении информации о сервере: {e}")
        await update.callback_query.answer("❌ Ошибка при получении данных", show_alert=True)


async def players_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить список игроков"""
    try:
        players = await palworld_api.get_players()
        
        if not players:
            message = "👥 **Список игроков**\n\nНа сервере нет игроков."
        else:
            message = f"👥 **Список игроков** ({len(players)})\n\n"
            for i, player in enumerate(players, 1):
                name = player.get('name', 'Unknown')
                player_id = player.get('playerId', 'N/A')
                message += f"{i}. **{name}**\n   ID: `{player_id}`\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="players_list")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка игроков: {e}")
        await update.callback_query.answer("❌ Ошибка при получении данных", show_alert=True)


async def announce_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос на ввод объявления"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "📢 **Отправить объявление**\n\n"
        "Введите текст объявления в следующем сообщении.\n"
        "Используйте команду: /announce <текст>"
    )


async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить объявление на сервер"""
    if not context.args:
        await update.message.reply_text(
            "❌ Используйте: /announce <текст объявления>"
        )
        return
    
    message = " ".join(context.args)
    try:
        await palworld_api.announce(message)
        await update.message.reply_text(f"✅ Объявление отправлено: {message}")
    except Exception as e:
        logger.error(f"Ошибка при отправке объявления: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def server_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню управления сервером"""
    keyboard = [
        [InlineKeyboardButton("💾 Сохранить мир", callback_data="save_world")],
        [InlineKeyboardButton("🛑 Остановить сервер", callback_data="shutdown_confirm")],
        [InlineKeyboardButton("⚠️ Принудительная остановка", callback_data="force_stop_confirm")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🖥️ **Управление сервером**\n\n"
        "⚠️ Будьте осторожны с операциями остановки сервера!",
        reply_markup=reply_markup
    )


async def save_world(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить мир"""
    try:
        await palworld_api.save_world()
        await update.callback_query.answer("✅ Мир сохранён!")
    except Exception as e:
        logger.error(f"Ошибка при сохранении мира: {e}")
        await update.callback_query.answer("❌ Ошибка при сохранении", show_alert=True)


async def shutdown_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение остановки сервера"""
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="shutdown_yes")],
        [InlineKeyboardButton("❌ Отмена", callback_data="server_manage")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "⚠️ **Подтверждение остановки сервера**\n\n"
        "Вы уверены, что хотите остановить сервер?",
        reply_markup=reply_markup
    )


async def shutdown_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Остановить сервер"""
    try:
        await palworld_api.shutdown(waittime=10, message="Сервер будет остановлен через 10 секунд")
        await update.callback_query.answer("✅ Сервер будет остановлен через 10 секунд")
    except Exception as e:
        logger.error(f"Ошибка при остановке сервера: {e}")
        await update.callback_query.answer("❌ Ошибка при остановке", show_alert=True)


async def force_stop_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение принудительной остановки"""
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="force_stop_yes")],
        [InlineKeyboardButton("❌ Отмена", callback_data="server_manage")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "⚠️ **Принудительная остановка сервера**\n\n"
        "⚠️ ВНИМАНИЕ: Это немедленно остановит сервер без сохранения!\n"
        "Вы уверены?",
        reply_markup=reply_markup
    )


async def force_stop_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принудительно остановить сервер"""
    try:
        await palworld_api.force_stop()
        await update.callback_query.answer("✅ Сервер принудительно остановлен")
    except Exception as e:
        logger.error(f"Ошибка при принудительной остановке: {e}")
        await update.callback_query.answer("❌ Ошибка при остановке", show_alert=True)


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    # Проверяем, является ли пользователь администратором
    user = update.effective_user
    admin_usernames = settings.get_admin_usernames()
    is_admin = user and user.username and user.username.lower() in admin_usernames
    
    # Формируем URL для Mini App (Telegram требует HTTPS)
    web_app_url = settings.web_server_url
    if web_app_url.startswith('http://'):
        web_app_url = web_app_url.replace('http://', 'https://', 1)
    
    # Добавляем параметр admin для администратора
    if is_admin:
        separator = '&' if '?' in web_app_url else '?'
        web_app_url = f"{web_app_url}{separator}admin=true"
    
    keyboard = [
        [InlineKeyboardButton("📱 Открыть Mini App", web_app=WebAppInfo(url=web_app_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🎮 Добро пожаловать в бот управления сервером Palworld!\n\n"
        "📱 Mini App позволяет:\n"
        "• Проверить онлайн сервера\n"
        "• Просмотреть карту с игроками\n"
        "• Узнать статус и статистику сервера"
    )
    
    if is_admin:
        welcome_text += "\n\n🔐 Вы вошли как администратор"
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        welcome_text,
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    data = query.data
    
    handlers = {
        "server_info": server_info,
        "players_list": players_list,
        "announce": announce_prompt,
        "server_manage": server_manage,
        "save_world": save_world,
        "shutdown_confirm": shutdown_confirm,
        "shutdown_yes": shutdown_yes,
        "force_stop_confirm": force_stop_confirm,
        "force_stop_yes": force_stop_yes,
        "back_to_menu": back_to_menu,
    }
    
    handler = handlers.get(data)
    if handler:
        await handler(update, context)
    else:
        await query.answer("Неизвестная команда")


def main():
    """Запуск бота"""
    # Создание приложения с увеличенными таймаутами
    from telegram.request import HTTPXRequest
    
    # Настройка Request с увеличенными таймаутами
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30.0,
        write_timeout=30.0,
        connect_timeout=30.0,
        pool_timeout=30.0
    )
    
    application = Application.builder().token(settings.telegram_bot_token).request(request).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("announce", announce_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запуск бота с обработкой ошибок
    logger.info("Бот запущен...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        logger.info("Попытка переподключения через 10 секунд...")
        import time
        time.sleep(10)
        # Повторная попытка
        main()


if __name__ == "__main__":
    main()

