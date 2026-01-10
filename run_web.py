"""
Запуск только веб-сервера (без бота и без No-IP логики).
Использует настройки из config.py и, при наличии, SSL-сертификаты.
"""
from pathlib import Path

import uvicorn

from config import settings


def main():
    print("=" * 70)
    print("🌐 ЗАПУСК ТОЛЬКО ВЕБ-СЕРВЕРА")
    print("=" * 70)
    print()

    ssl_keyfile = None
    ssl_certfile = None

    # Если явно указаны пути к сертификатам – используем их
    if settings.ssl_cert_path and settings.ssl_key_path:
        cert_path = Path(settings.ssl_cert_path)
        key_path = Path(settings.ssl_key_path)
        if cert_path.exists() and key_path.exists():
            ssl_certfile = str(cert_path)
            ssl_keyfile = str(key_path)
            print(f"🔐 SSL сертификаты найдены: {ssl_certfile}")

    ssl_kwargs = {}
    if ssl_keyfile and ssl_certfile:
        ssl_kwargs = {
            "ssl_keyfile": ssl_keyfile,
            "ssl_certfile": ssl_certfile,
        }

    print(f"🚀 Запуск веб-сервера на {settings.web_server_host}:{settings.web_server_port}...")
    print()

    uvicorn.run(
        "web_server:app",
        host=settings.web_server_host,
        port=settings.web_server_port,
        log_level="info",
        **ssl_kwargs,
    )


if __name__ == "__main__":
    main()


