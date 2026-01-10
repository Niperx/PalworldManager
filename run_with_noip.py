"""
Автоматический запуск проекта с No-IP доменом (без Docker)
Запускает: веб-сервер -> обновление настроек бота -> бот
"""
import multiprocessing
import time
import sys
import signal
import uvicorn
from pathlib import Path
from config import settings
from scripts.noip_updater import update_bot_url, get_certificate_paths


def run_web_server(ssl_keyfile=None, ssl_certfile=None):
    """Запуск веб-сервера с поддержкой SSL"""
    ssl_kwargs = {}
    
    if ssl_keyfile and ssl_certfile:
        ssl_kwargs = {
            "ssl_keyfile": ssl_keyfile,
            "ssl_certfile": ssl_certfile
        }
    
    uvicorn.run(
        "web_server:app",
        host=settings.web_server_host,
        port=settings.web_server_port,
        log_level="info",
        **ssl_kwargs
    )


def run_bot():
    """Запуск Telegram бота"""
    from bot.main import main
    main()


def main():
    """Главная функция"""
    print("="*70)
    print("🚀 АВТОМАТИЧЕСКИЙ ЗАПУСК С NO-IP")
    print("="*70)
    print()
    
    # Проверяем настройки No-IP hostname
    if not settings.noip_hostname:
        print("❌ Ошибка: NOIP_HOSTNAME не указан в .env файле")
        print("\n📝 Настройте в .env файле:")
        print("   NOIP_HOSTNAME=yourhostname.ddns.net")
        sys.exit(1)
    
    # Словарь для хранения процессов
    processes = {}
    
    def cleanup(signum=None, frame=None):
        """Очистка при завершении"""
        print("\n\n🛑 Остановка сервисов...")
        for name, process in processes.items():
            if process and process.is_alive():
                print(f"   Остановка {name}...")
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        # Шаг 1: Проверяем наличие SSL сертификатов и формируем URL
        ssl_keyfile = None
        ssl_certfile = None
        use_https = False
        
        if settings.ssl_cert_path and settings.ssl_key_path:
            cert_path = Path(settings.ssl_cert_path)
            key_path = Path(settings.ssl_key_path)
            if cert_path.exists() and key_path.exists():
                ssl_certfile = str(cert_path)
                ssl_keyfile = str(key_path)
                use_https = True
                print(f"🔐 SSL сертификаты найдены: {ssl_certfile}")
        
        if not use_https and settings.noip_hostname:
            cert_path, key_path = get_certificate_paths(settings.noip_hostname)
            if cert_path and key_path and cert_path.exists() and key_path.exists():
                ssl_certfile = str(cert_path)
                ssl_keyfile = str(key_path)
                use_https = True
                print(f"🔐 SSL сертификаты автоматически найдены для {settings.noip_hostname}")
        
        # Формируем URL (HTTPS если есть SSL, иначе HTTP)
        if use_https:
            noip_url = f"https://{settings.noip_hostname}"
        else:
            noip_url = f"http://{settings.noip_hostname}"
            print("⚠️  SSL сертификаты не найдены, используется HTTP")
            print("   Telegram Mini App требует HTTPS, настройте SSL сертификат")
        
        print()
        
        # Шаг 2: Запускаем веб-сервер
        print("📡 Шаг 1/3: Запуск веб-сервера...")
        processes['web'] = multiprocessing.Process(
            target=run_web_server,
            args=(ssl_keyfile, ssl_certfile),
            daemon=True
        )
        processes['web'].start()
        
        # Ждем немного, чтобы сервер запустился
        print(f"   Ожидание запуска сервера на порту {settings.web_server_port}...")
        time.sleep(3)
        
        if not processes['web'].is_alive():
            print("❌ Ошибка: веб-сервер не запустился")
            cleanup()
            return
        
        print(f"✅ Веб-сервер запущен на порту {settings.web_server_port}")
        print()
        
        # Шаг 3: Обновляем настройки бота
        print("🔧 Шаг 2/3: Обновление настроек бота...")
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
        
        # Шаг 4: Запускаем бота
        print("🤖 Шаг 3/3: Запуск Telegram бота...")
        processes['bot'] = multiprocessing.Process(
            target=run_bot,
            daemon=True
        )
        processes['bot'].start()
        
        time.sleep(2)
        
        if not processes['bot'].is_alive():
            print("❌ Ошибка: бот не запустился")
            cleanup()
            return
        
        print("✅ Бот запущен")
        print()
        print("="*70)
        print("✅ ВСЁ ЗАПУЩЕНО УСПЕШНО!")
        print("="*70)
        print()
        print(f"🌐 Веб-сервер: {noip_url}")
        print(f"🤖 Telegram бот: запущен и работает")
        print()
        print("Нажмите Ctrl+C для остановки")
        print()
        
        # Ждем завершения
        while True:
            time.sleep(1)
            # Проверяем, что процессы ещё работают
            if processes['web'] and not processes['web'].is_alive():
                print("⚠️  Веб-сервер остановился")
                cleanup()
            if processes['bot'] and not processes['bot'].is_alive():
                print("⚠️  Бот остановился")
                cleanup()
    
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        cleanup()


if __name__ == "__main__":
    main()

