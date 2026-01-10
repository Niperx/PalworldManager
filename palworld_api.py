"""
Модуль для работы с Palworld REST API
"""
import aiohttp
import base64
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PalworldAPI:
    """Класс для взаимодействия с Palworld REST API"""
    
    def __init__(self, server_url: str, admin_password: str):
        """
        Инициализация API клиента
        
        Args:
            server_url: URL сервера Palworld (например, http://localhost:8212)
            admin_password: Пароль администратора
        """
        self.server_url = server_url.rstrip('/')
        self.admin_password = admin_password
        # Пробуем разные варианты базового URL
        # Некоторые версии используют /v1/api, другие - прямой путь
        self.base_url = self.server_url
        self.api_paths = [
            "",  # Прямой путь (например, /announce) - пробуем первым
            "/v1/api",  # Версия с /v1/api префиксом
            "/api",  # Версия с /api префиксом
            "/v1",  # Версия с /v1 префиксом
        ]
        
        # Создаём Basic Auth заголовок
        credentials = f"admin:{admin_password}".encode()
        auth_token = base64.b64encode(credentials).decode()
        self.headers = {
            "Authorization": f"Basic {auth_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Выполняет HTTP запрос к API
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: Конечная точка API
            **kwargs: Дополнительные параметры для запроса
            
        Returns:
            Ответ от API в виде словаря
        """
        # Убираем начальный слэш из endpoint
        endpoint = endpoint.lstrip('/')
        
        # Пробуем разные варианты путей
        last_error = None
        for api_path in self.api_paths:
            if api_path:
                url = f"{self.base_url}{api_path}/{endpoint}" if endpoint else f"{self.base_url}{api_path}"
            else:
                url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method, 
                        url, 
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=10),
                        **kwargs
                    ) as response:
                        logger.debug(f"API {method} {url} -> {response.status}")
                        # Успешные статусы: 200, 201, 202, 204
                        if response.status in [200, 201, 202, 204]:
                            # Пробуем получить JSON, если есть тело ответа
                            try:
                                if response.status == 204:
                                    return {"status": "success"}
                                
                                # Пробуем прочитать тело ответа
                                try:
                                    text = await response.text()
                                    if text:
                                        # Пробуем распарсить как JSON
                                        try:
                                            import json
                                            return json.loads(text)
                                        except:
                                            # Если не JSON, но статус успешный - считаем успехом
                                            return {"status": "success", "message": text}
                                    else:
                                        # Пустое тело, но статус успешный
                                        return {"status": "success"}
                                except Exception as read_error:
                                    # Если не удалось прочитать тело, но статус успешный - считаем успехом
                                    return {"status": "success"}
                            except Exception as parse_error:
                                # Если не удалось обработать ответ, но статус успешный - считаем успехом
                                return {"status": "success"}
                        elif response.status == 404:
                            # Пробуем следующий путь
                            last_error = f"404 for {url}"
                            continue
                        else:
                            # Для других статусов пробуем прочитать ошибку
                            try:
                                error_text = await response.text()
                                last_error = f"API Error {response.status} for {url}: {error_text}"
                            except:
                                last_error = f"API Error {response.status} for {url}"
                            continue
            except Exception as e:
                last_error = f"Exception for {url}: {str(e)}"
                continue
        
        # Если все пути не сработали, выбрасываем последнюю ошибку
        raise Exception(f"All API paths failed. Last error: {last_error}")
    
    async def test_connection(self) -> bool:
        """Проверка подключения к серверу"""
        try:
            # Пробуем простой запрос к корню API
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status in [200, 404]  # 404 тоже означает, что сервер отвечает
        except Exception:
            return False
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Получить информацию о сервере"""
        return await self._request("GET", "/info")
    
    async def get_players(self) -> List[Dict[str, Any]]:
        """Получить список игроков"""
        return await self._request("GET", "/players")
    
    async def get_server_settings(self) -> Dict[str, Any]:
        """Получить настройки сервера"""
        return await self._request("GET", "/settings")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Получить метрики сервера"""
        return await self._request("GET", "/metrics")
    
    async def announce(self, message: str) -> Dict[str, Any]:
        """
        Отправить объявление на сервер
        
        Args:
            message: Текст объявления
        """
        return await self._request("POST", "/announce", json={"message": message})
    
    async def kick_player(self, userid: str, message: str = "") -> Dict[str, Any]:
        """
        Выгнать игрока с сервера
        
        Args:
            userid: ID игрока (Steam ID)
            message: Сообщение для игрока (опционально)
        """
        return await self._request("POST", "/kick", json={
            "userid": userid,
            "message": message
        })
    
    async def ban_player(self, userid: str) -> Dict[str, Any]:
        """
        Забанить игрока
        
        Args:
            userid: ID игрока (Steam ID)
        """
        return await self._request("POST", "/ban", json={"userid": userid})
    
    async def unban_player(self, userid: str) -> Dict[str, Any]:
        """
        Разбанить игрока
        
        Args:
            userid: ID игрока (Steam ID)
        """
        return await self._request("POST", "/unban", json={"userid": userid})
    
    async def save_world(self) -> Dict[str, Any]:
        """Сохранить мир"""
        return await self._request("POST", "/save")
    
    async def shutdown(self, waittime: int = 1, message: str = "") -> Dict[str, Any]:
        """
        Остановить сервер
        
        Args:
            waittime: Время ожидания в секундах перед остановкой
            message: Сообщение для игроков
        """
        return await self._request("POST", "/shutdown", json={
            "waittime": waittime,
            "message": message
        })
    
    async def force_stop(self) -> Dict[str, Any]:
        """Принудительно остановить сервер"""
        return await self._request("POST", "/stop")

