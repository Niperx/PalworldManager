"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Telegram Bot
    telegram_bot_token: str
    admin_usernames: Optional[str] = None  # Список администраторов через запятую (например, "niperx,admin1,admin2")
    
    # Palworld Server
    palworld_server_url: str = "http://localhost:8212"
    palworld_admin_password: str
    
    # Web Server
    web_server_host: str = "0.0.0.0"
    web_server_port: int = 8000
    web_server_url: str = "http://localhost:8000"
    
    # Dynamic DNS Configuration (optional - for No-IP)
    noip_hostname: Optional[str] = None  # Полное имя хоста (например, 'mysite.ddns.net')
    noip_username: Optional[str] = None  # Логин No-IP
    noip_password: Optional[str] = None  # Пароль No-IP
    
    # SSL Configuration (optional - for Let's Encrypt)
    ssl_cert_path: Optional[str] = None  # Путь к SSL сертификату (fullchain.pem)
    ssl_key_path: Optional[str] = None  # Путь к SSL ключу (privkey.pem)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Игнорировать дополнительные поля из .env
    
    def get_admin_usernames(self) -> list[str]:
        """Возвращает список администраторов в нижнем регистре"""
        if not self.admin_usernames:
            return []
        return [username.strip().lower() for username in self.admin_usernames.split(',') if username.strip()]


# Глобальный экземпляр настроек
settings = Settings()

