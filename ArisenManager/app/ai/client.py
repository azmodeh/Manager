import os
import time
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from ..utils.config_loader import config_loader

class AIClient:
    def __init__(self) -> None:
        self.config = config_loader.load_config("ai.yml")
        self.current_endpoint = "primary"
        self.last_failure_time = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config["policy"]["timeout_ms"] / 1000)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    def _get_endpoint_config(self, endpoint: str) -> Dict[str, str]:
        endpoint_config = self.config[endpoint]
        return {
            "base_url": os.getenv(endpoint_config["base_url_env"]),
            "api_key": os.getenv(endpoint_config["api_key_env"]),
            "model": os.getenv(endpoint_config["model_id_env"])
        }
    
    def _is_endpoint_available(self, endpoint: str) -> bool:
        if endpoint not in self.last_failure_time:
            return True
        
        cooldown = self.config["policy"]["cooldown_sec"]
        return time.time() - self.last_failure_time[endpoint] > cooldown
    
    async def _make_request(self, endpoint: str, message: str) -> Optional[str]:
        if not self._is_endpoint_available(endpoint):
            return None
        
        config = self._get_endpoint_config(endpoint)
        if not all(config.values()):
            return None
        
        session = await self._get_session()
        
        try:
            start_time = time.time()
            
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": config["model"],
                "messages": [{"role": "user", "content": message}],
                "max_tokens": self.config["policy"]["max_tokens"],
                "temperature": self.config["policy"]["temperature"]
            }
            
            url = f"{config['base_url'].rstrip('/')}/chat/completions"
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    latency = (time.time() - start_time) * 1000
                    
                    if latency > self.config["policy"]["switch_threshold_ms"]:
                        self.last_failure_time[endpoint] = time.time()
                        return None
                    
                    return data["choices"][0]["message"]["content"]
                else:
                    self.last_failure_time[endpoint] = time.time()
                    return None
                    
        except Exception:
            self.last_failure_time[endpoint] = time.time()
            return None
    
    async def generate_response(self, message: str, chat_id: int = 0, user_id: int = 0) -> str:
        endpoints = ["primary", "fallback_1", "fallback_2"]
        
        for endpoint in endpoints:
            response = await self._make_request(endpoint, message)
            if response:
                # Clean response
                clean_response = response.strip()
                
                # Apply length limit
                max_length = self.config.get("policy", {}).get("max_tokens", 200)
                if len(clean_response) > max_length:
                    clean_response = clean_response[:max_length] + "..."
                
                return clean_response
        
        return self.config["errors"]["all_failed"]
    
    async def close(self) -> None:
        if self.session:
            await self.session.close()

ai_client = AIClient()