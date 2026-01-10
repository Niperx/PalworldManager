"""
Скрипт для запуска Telegram бота с обновлением No-IP URL
"""
import sys
from pathlib import Path
from config import settings
from scripts.noip_updater import update_bot_url, get_certificate_paths

def main():
    """Главная функция - обновляет URL из No-IP и запускает бота"""
    print("="*70)
    print("🤖 ЗАПУСК TELEGRAM БОТА С NO-IP")
    print("="*70)
    print()
    
    # Проверяем настройки No-IP hostname
    if not settings.noip_hostname:
        print("❌ Ошибка: NOIP_HOSTNAME не указан в .env файле")
        print("\n📝 Настройте в .env файле:")
        print("   NOIP_HOSTNAME=yourhostname.ddns.net")
        sys.exit(1)
    
    # Проверяем наличие SSL сертификатов и формируем URL
    ssl_keyfile = None
    ssl_certfile = None
    use_https = False
    
    if settings.ssl_cert_path and settings.ssl_key_path:
        cert_path = Path(settings.ssl_cert_path)
        key_path = Path(settings.ssl_key_path)
        if cert_path.exists() and key_path.exists():
            use_https = True
    
    if not use_https and settings.noip_hostname:
        cert_path, key_path = get_certificate_paths(settings.noip_hostname)
        if cert_path and key_path and cert_path.exists() and key_path.exists():
            use_https = True
    
    # Формируем URL (HTTPS если есть SSL, иначе HTTP)
    if use_https:
        noip_url = f"https://{settings.noip_hostname}"
        print(f"🔐 Используется HTTPS: {noip_url}")
    else:
        noip_url = f"http://{settings.noip_hostname}"
        print(f"⚠️  SSL сертификаты не найдены, используется HTTP: {noip_url}")
        print("   Telegram Mini App требует HTTPS, настройте SSL сертификат")
    
    print()
    
    # Обновляем настройки бота
    print("🔧 Обновление настроек бота...")
    print(f"   URL: {noip_url}")
    
    env_updated, telegram_updated = update_bot_url(
        noip_url,
        update_env=True,
        update_telegram=True
    )
    
    if env_updated:
        print("✅ URL обновлён в .env файле")
    if telegram_updated:
        print("✅ Кнопка Mini App обновлена в Telegram боте")
    
    print()
    
    # Запускаем бота
    print("🤖 Запуск Telegram бота...")
    print()
    
    from bot.main import main as bot_main
    bot_main()


if __name__ == "__main__":
    main()

