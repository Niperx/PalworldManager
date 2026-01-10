"""
Модуль для автоматического обновления IP адреса в No-IP
No-IP - бесплатный динамический DNS сервис
"""
import requests
import time
import logging
import sys
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)


def get_current_ip():
    """Получает текущий внешний IP адрес"""
    services = [
        'https://api.ipify.org',
        'https://icanhazip.com',
        'https://ifconfig.me/ip',
        'https://api.myip.com',
    ]
    
    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                ip = response.text.strip()
                # Проверяем, что это валидный IP
                if ip and '.' in ip and len(ip.split('.')) == 4:
                    return ip
        except Exception as e:
            logger.debug(f"Не удалось получить IP с {service}: {e}")
            continue
    
    return None


def update_noip(hostname, username, password, ip=None):
    """
    Обновляет IP адрес в No-IP
    
    Args:
        hostname: Полное имя хоста (например, 'mysite.ddns.net')
        username: Логин No-IP
        password: Пароль No-IP
        ip: IP адрес (опционально, если None - определяется автоматически)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not hostname or not username or not password:
        return False, "Хост, логин и пароль обязательны"
    
    url = 'https://dynupdate.no-ip.com/nic/update'
    params = {
        'hostname': hostname,
    }
    
    if ip:
        params['myip'] = ip
    
    # No-IP использует Basic Authentication
    auth = (username, password)
    
    try:
        response = requests.get(url, params=params, auth=auth, timeout=10)
        
        if response.status_code == 200:
            result = response.text.strip()
            
            # No-IP возвращает различные коды ответа
            if result.startswith('good') or result.startswith('nochg'):
                # good - IP обновлен успешно
                # nochg - IP не изменился, но запрос успешен
                return True, f"DNS обновлен: {hostname}"
            elif result.startswith('nohost'):
                return False, "Хост не существует или не принадлежит вам"
            elif result.startswith('badauth'):
                return False, "Неверный логин или пароль"
            elif result.startswith('badagent'):
                return False, "Неверный User-Agent (проблема с запросом)"
            elif result.startswith('!donator'):
                return False, "Требуется платная подписка для этой функции"
            elif result.startswith('abuse'):
                return False, "Хост заблокирован из-за злоупотребления"
            elif result.startswith('911'):
                return False, "Временная ошибка сервера No-IP, попробуйте позже"
            else:
                return False, f"Неожиданный ответ: {result}"
        else:
            return False, f"HTTP ошибка: {response.status_code}"
            
    except Exception as e:
        return False, f"Ошибка запроса: {str(e)}"


def start_noip_updater(hostname, username, password, check_interval=300, on_update_callback=None):
    """
    Запускает периодическое обновление IP в No-IP
    
    Args:
        hostname: Полное имя хоста (например, 'mysite.ddns.net')
        username: Логин No-IP
        password: Пароль No-IP
        check_interval: Интервал проверки в секундах (по умолчанию 5 минут)
        on_update_callback: Функция-колбэк, вызываемая после успешного обновления
                           Принимает параметры: (hostname, ip)
    """
    logger.info(f"Запуск No-IP обновления для {hostname}")
    
    last_ip = None
    noip_url = f"https://{hostname}"
    
    while True:
        try:
            current_ip = get_current_ip()
            
            if not current_ip:
                logger.warning("Не удалось определить текущий IP адрес")
                time.sleep(check_interval)
                continue
            
            # Обновляем только если IP изменился
            if current_ip != last_ip:
                logger.info(f"Обнаружен IP: {current_ip} (предыдущий: {last_ip})")
                
                success, message = update_noip(hostname, username, password, current_ip)
                
                if success:
                    logger.info(f"✅ {message}")
                    last_ip = current_ip
                    
                    # Вызываем колбэк после успешного обновления
                    if on_update_callback:
                        try:
                            on_update_callback(noip_url, current_ip)
                        except Exception as e:
                            logger.error(f"Ошибка в колбэке обновления: {e}")
                else:
                    logger.error(f"❌ Ошибка обновления No-IP: {message}")
            else:
                logger.debug(f"IP не изменился: {current_ip}")
            
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("Остановка No-IP обновления...")
            break
        except Exception as e:
            logger.error(f"Ошибка в цикле обновления: {e}")
            time.sleep(check_interval)


def get_certificate_paths(domain):
    """Возвращает пути к SSL сертификатам для домена"""
    if not domain:
        return None, None
    
    # Сначала проверяем локальную папку certs (для Docker на Windows)
    local_archive_dir = Path("certs") / "archive" / domain
    
    # В Let's Encrypt файлы в live - это симлинки на archive
    # На Windows симлинки могут не работать, поэтому проверяем archive напрямую
    if local_archive_dir.exists():
        fullchain = local_archive_dir / "fullchain1.pem"
        privkey = local_archive_dir / "privkey1.pem"
        
        if fullchain.exists() and privkey.exists():
            return fullchain, privkey
    
    # Пробуем через live (может работать если симлинки поддерживаются)
    local_live_dir = Path("certs") / "live" / domain
    if local_live_dir.exists():
        cert_file = local_live_dir / "fullchain.pem"
        key_file = local_live_dir / "privkey.pem"
        try:
            if cert_file.exists() and key_file.exists():
                return cert_file, key_file
        except (OSError, PermissionError):
            pass
    
    # Стандартные пути Let's Encrypt на Linux
    cert_dir = Path("/etc/letsencrypt/live") / domain
    if cert_dir.exists():
        cert_file = cert_dir / "fullchain.pem"
        key_file = cert_dir / "privkey.pem"
        return cert_file, key_file
    
    # Возвращаем пути к archive (даже если файлы не найдены)
    return local_archive_dir / "fullchain1.pem", local_archive_dir / "privkey1.pem"


def update_env_file(url: str, env_file: str = ".env"):
    """
    Обновляет WEB_SERVER_URL в .env файле
    
    Args:
        url: Новый URL для веб-сервера
        env_file: Путь к .env файлу
    
    Returns:
        bool: True если успешно обновлено
    """
    import re
    env_path = Path(env_file)
    
    if not env_path.exists():
        logger.warning(f"Файл {env_file} не найден")
        return False
    
    try:
        # Читаем содержимое файла
        content = env_path.read_text(encoding='utf-8')
        
        # Ищем строку с WEB_SERVER_URL
        pattern = r'^WEB_SERVER_URL=.*$'
        replacement = f'WEB_SERVER_URL={url}'
        
        if re.search(pattern, content, re.MULTILINE):
            # Заменяем существующую строку
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        else:
            # Добавляем новую строку, если её нет
            if not content.endswith('\n'):
                content += '\n'
            new_content = content + f'{replacement}\n'
        
        # Записываем обратно
        env_path.write_text(new_content, encoding='utf-8')
        logger.info(f"✅ Обновлён {env_file}: WEB_SERVER_URL={url}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении {env_file}: {e}")
        return False


async def update_telegram_bot_menu(url: str, bot_token: str = None):
    """
    Обновляет кнопку меню в Telegram боте с новым URL Mini App
    
    Args:
        url: Новый URL для Mini App
        bot_token: Токен бота (если не указан, берётся из settings)
    
    Returns:
        bool: True если успешно обновлено
    """
    # Telegram требует HTTPS для Web App
    if url.startswith('http://'):
        url = url.replace('http://', 'https://', 1)
    
    if bot_token is None:
        bot_token = settings.telegram_bot_token
    
    if not bot_token:
        logger.warning("Токен бота не найден в настройках")
        return False
    
    try:
        from telegram import Bot, MenuButtonWebApp, WebAppInfo
        from telegram.error import TelegramError
        
        bot = Bot(token=bot_token)
        
        # Устанавливаем кнопку меню с Mini App
        menu_button = MenuButtonWebApp(
            text="📱 Открыть Mini App",
            web_app=WebAppInfo(url=url)
        )
        
        await bot.set_chat_menu_button(menu_button=menu_button)
        logger.info(f"✅ Обновлена кнопка меню в Telegram боте: {url}")
        return True
        
    except Exception as e:
        logger.warning(f"Не удалось обновить кнопку меню в боте: {e}")
        return False


def update_bot_url(url: str, update_env: bool = True, update_telegram: bool = True):
    """
    Обновляет URL веб-сервера в .env и настраивает Mini App в Telegram боте
    
    Args:
        url: Новый URL для веб-сервера
        update_env: Обновить ли .env файл
        update_telegram: Обновить ли кнопку меню в Telegram боте
    
    Returns:
        tuple: (env_updated, telegram_updated)
    """
    env_updated = False
    telegram_updated = False
    
    if update_env:
        env_updated = update_env_file(url)
    
    if update_telegram:
        import asyncio
        try:
            telegram_updated = asyncio.run(update_telegram_bot_menu(url))
        except Exception as e:
            logger.warning(f"Ошибка при обновлении Telegram бота: {e}")
    
    return env_updated, telegram_updated


def update_bot_url_callback(noip_url, current_ip):
    """Колбэк для обновления URL в боте после обновления No-IP"""
    try:
        # Проверяем наличие SSL сертификата для определения протокола
        use_https = False
        if settings.ssl_cert_path and settings.ssl_key_path:
            cert_path = Path(settings.ssl_cert_path)
            key_path = Path(settings.ssl_key_path)
            if cert_path.exists() and key_path.exists():
                use_https = True
        elif settings.noip_hostname:
            cert_path, key_path = get_certificate_paths(settings.noip_hostname)
            if cert_path and key_path and cert_path.exists() and key_path.exists():
                use_https = True
        
        # Формируем правильный URL
        if use_https and noip_url.startswith("http://"):
            noip_url = noip_url.replace("http://", "https://", 1)
        elif not use_https and noip_url.startswith("https://"):
            noip_url = noip_url.replace("https://", "http://", 1)
        
        logger.info(f"Обновление URL в настройках бота: {noip_url}")
        env_updated, telegram_updated = update_bot_url(
            noip_url,
            update_env=True,
            update_telegram=True
        )
        
        if env_updated:
            logger.info(f"✅ URL обновлён в .env файле: {noip_url}")
        if telegram_updated:
            logger.info(f"✅ Кнопка Mini App обновлена в Telegram боте")
    except Exception as e:
        logger.error(f"Ошибка обновления URL бота: {e}")


def main():
    """Главная функция для запуска обновления No-IP"""
    import sys
    
    if not settings.noip_hostname or not settings.noip_username or not settings.noip_password:
        print("❌ Ошибка: No-IP настройки не заполнены")
        print("\n📝 Настройте в .env файле:")
        print("   NOIP_HOSTNAME=yourhostname.ddns.net")
        print("   NOIP_USERNAME=your-username")
        print("   NOIP_PASSWORD=your-password")
        print("\n💡 Зарегистрируйтесь на https://www.noip.com/")
        print("   Создайте хост в разделе Dynamic DNS")
        sys.exit(1)
    
    print("="*70)
    print("🌐 NO-IP - БЕСПЛАТНЫЙ ДИНАМИЧЕСКИЙ DNS")
    print("="*70)
    print(f"🌐 Хост: {settings.noip_hostname}")
    print(f"👤 Пользователь: {settings.noip_username}")
    print(f"⏱️  Интервал проверки: 5 минут")
    print()
    print("💡 Нажмите Ctrl+C для остановки")
    print("="*70)
    print()
    
    try:
        start_noip_updater(
            hostname=settings.noip_hostname,
            username=settings.noip_username,
            password=settings.noip_password,
            check_interval=300,  # 5 минут
            on_update_callback=update_bot_url_callback
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Остановка No-IP обновления...")


if __name__ == "__main__":
    main()

