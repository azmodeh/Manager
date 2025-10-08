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
        env_config = config_loader.load_config("env.yml")
        defaults = env_config.get("defaults", {})
        ai_defaults = defaults.get("ai", {})
        ai_keys = env_config.get("ai", {})
        
        if endpoint == "primary":
            return {
                "base_url": ai_defaults.get("primary_base_url"),
                "api_key": ai_keys.get("openrouter_key"),
                "model": ai_defaults.get("primary_model")
            }
        elif endpoint == "fallback_1":
            return {
                "base_url": ai_defaults.get("fallback1_base_url"),
                "api_key": ai_keys.get("gemini_key"),
                "model": ai_defaults.get("fallback1_model")
            }
        else:
            return {
                "base_url": ai_defaults.get("fallback2_base_url"),
                "api_key": ai_keys.get("mistral_key"),
                "model": ai_defaults.get("fallback2_model")
            }
    
    def _is_endpoint_available(self, endpoint: str) -> bool:
        if endpoint not in self.last_failure_time:
            return True
        
        cooldown = self.config["policy"]["cooldown_sec"]
        return time.time() - self.last_failure_time[endpoint] > cooldown
    
    async def _make_request(self, endpoint: str, message: str) -> Optional[str]:
        import logging
        logger = logging.getLogger(__name__)
        
        if not self._is_endpoint_available(endpoint):
            logger.warning(f"Endpoint {endpoint} not available (cooldown)")
            return None
        
        config = self._get_endpoint_config(endpoint)
        if not all(config.values()):
            logger.warning(f"Endpoint {endpoint} missing config: {config}")
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
            
            logger.info(f"Making request to {url} with model {config['model']}")
            async with session.post(url, json=payload, headers=headers) as response:
                logger.info(f"Response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    latency = (time.time() - start_time) * 1000
                    logger.info(f"Request latency: {latency}ms")
                    
                    if latency > self.config["policy"]["switch_threshold_ms"]:
                        logger.warning(f"Latency too high for {endpoint}: {latency}ms")
                        self.last_failure_time[endpoint] = time.time()
                        return None
                    
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"AI response content: {content[:100]}...")
                    return content
                else:
                    logger.error(f"HTTP error {response.status} from {endpoint}")
                    self.last_failure_time[endpoint] = time.time()
                    return None
                    
        except Exception as e:
            logger.error(f"Exception in {endpoint} request: {e}")
            self.last_failure_time[endpoint] = time.time()
            return None
    
    async def generate_response(self, message: str, chat_id: int = 0, user_id: int = 0) -> str:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"AI client generating response for message: {message[:50]}...")
        endpoints = ["primary", "fallback_1", "fallback_2"]
        
        for endpoint in endpoints:
            logger.info(f"Trying endpoint: {endpoint}")
            config = self._get_endpoint_config(endpoint)
            logger.info(f"Endpoint config - base_url: {config['base_url']}, model: {config['model']}, has_key: {bool(config['api_key'])}")
            
            response = await self._make_request(endpoint, message)
            if response:
                logger.info(f"Got response from {endpoint}: {response[:100]}...")
                # Clean response
                clean_response = response.strip()
                
                # Apply length limit
                max_length = self.config.get("policy", {}).get("max_tokens", 200)
                if len(clean_response) > max_length:
                    clean_response = clean_response[:max_length] + "..."
                
                return clean_response
            else:
                logger.warning(f"No response from {endpoint}")
        
        logger.error("All AI endpoints failed")
        return self.config["errors"]["all_failed"]
    
    async def close(self) -> None:
        if self.session:
            await self.session.close()

ai_client = AIClient()