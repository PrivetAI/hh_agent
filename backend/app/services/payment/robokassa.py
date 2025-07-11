import hashlib
import json
import logging
import os
from typing import Dict, Any, Optional
from urllib.parse import quote, urlencode
from ...core.config import settings

logger = logging.getLogger(__name__)

class RobokassaPaymentService:
    def __init__(self):
        self.merchant_login = settings.ROBOKASSA_MERCHANT_LOGIN
        self.base_url = "https://auth.robokassa.ru/Merchant/Index.aspx"
        
        # Принудительно устанавливаем тестовый режим для разработки
        # если явно не указано обратное
        env_test_mode = os.environ.get('ROBOKASSA_TEST_MODE', 'true').lower()
        self.test_mode = env_test_mode in ('true', '1', 'yes', 'on')
        
        logger.info(f"Initializing Robokassa: test_mode={self.test_mode}, merchant={self.merchant_login}")
        logger.info(f"Environment ROBOKASSA_TEST_MODE: {env_test_mode}")
        
        if self.test_mode:
            self.password1 = settings.ROBOKASSA_TEST_PASSWORD_1 or "BCd7XYGZ42m4cbeHX6be"
            self.password2 = settings.ROBOKASSA_TEST_PASSWORD_2 or "pjXW77PQV28NP2glvHfp"
            logger.info(f"Robokassa initialized in TEST mode")
        else:
            self.password1 = settings.ROBOKASSA_PASSWORD_1
            self.password2 = settings.ROBOKASSA_PASSWORD_2
            logger.info(f"Robokassa initialized in PRODUCTION mode")
        
        # Проверяем наличие паролей - но с более мягкой проверкой для разработки
        if not self.password1 or not self.password2:
            logger.warning(f"Robokassa passwords not fully configured for {'TEST' if self.test_mode else 'PROD'} mode")
            logger.warning(f"Using fallback values for development")
            # Используем заглушки для разработки
            if not self.password1:
                self.password1 = "dummy_password1"
            if not self.password2:
                self.password2 = "dummy_password2"

    def _generate_signature(self, *args) -> str:
        """Generate MD5 signature"""
        signature_string = ":".join(str(arg) for arg in args if arg is not None)
        logger.debug(f"Signature string: {signature_string}")
        signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
        logger.debug(f"Generated signature: {signature}")
        return signature

    def create_payment_link(
        self,
        payment_id: int,
        amount: float,
        description: str,
        user_email: str = None,
        receipt_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create payment link"""
        out_sum = f"{amount:.2f}"
        inv_id = str(payment_id)

        # Логируем режим работы
        logger.info(f"Creating payment link in {'TEST' if self.test_mode else 'PRODUCTION'} mode")
        
        # В тестовом режиме используем минимальный набор параметров
        if self.test_mode:
            # Только обязательные параметры для теста
            signature = self._generate_signature(
                self.merchant_login,
                out_sum,
                inv_id,
                self.password1
            )
            
            params = {
                "MerchantLogin": self.merchant_login,
                "OutSum": out_sum,
                "InvId": inv_id,
                "SignatureValue": signature,
                "IsTest": "1"
            }
            
            # Добавляем только Description в тестовом режиме
            if description:
                params["Description"] = description
                
        else:
            # Продакшн режим с полной поддержкой
            params = {
                "MerchantLogin": self.merchant_login,
                "OutSum": out_sum,
                "InvId": inv_id,
                "Description": description,
                "Culture": "ru",
                "Encoding": "utf-8",
            }
            
            if user_email:
                params["Email"] = user_email
            
            # Формируем части для подписи
            sig_parts = [self.merchant_login, out_sum, inv_id]
            
            # Добавляем чек в продакшн режиме
            if receipt_data:
                receipt_json = json.dumps(receipt_data, ensure_ascii=False, separators=(',', ':'))
                params["Receipt"] = receipt_json
                sig_parts.append(receipt_json)
            
            sig_parts.append(self.password1)
            
            signature = self._generate_signature(*sig_parts)
            params["SignatureValue"] = signature

        # Формируем URL
        logger.info(f"Creating payment URL with params: {list(params.keys())}")
        url = f"{self.base_url}?{urlencode(params, safe='')}"
        logger.info(f"Payment URL: {url[:100]}...")
        
        return url

    def verify_payment_result(self, data: Dict[str, Any]) -> bool:
        """Verify payment result signature (uses Password2)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        signature = data.get("SignatureValue", "").lower()
        
        if not all([out_sum, inv_id, signature]):
            logger.warning("Missing required fields for payment verification")
            return False
        
        # Базовая проверка подписи: OutSum:InvId:Password2
        expected = self._generate_signature(out_sum, inv_id, self.password2).lower()
        
        # Если есть shp_ параметры, нужно их учесть
        shp_params = sorted([(k, v) for k, v in data.items() if k.startswith('shp_')])
        if shp_params:
            sig_parts = [out_sum, inv_id]
            for key, value in shp_params:
                sig_parts.append(f"{key}={value}")
            sig_parts.append(self.password2)
            expected = self._generate_signature(*sig_parts).lower()
        
        result = signature == expected
        
        if not result:
            logger.warning(f"Signature mismatch. Expected: {expected}, Got: {signature}")
            logger.warning(f"Data: OutSum={out_sum}, InvId={inv_id}")
        
        return result

    def verify_success_url(self, data: Dict[str, Any]) -> bool:
        """Verify success URL signature (uses Password1)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        signature = data.get("SignatureValue", "").lower()
        
        if not all([out_sum, inv_id, signature]):
            return False
        
        # Базовая проверка подписи: OutSum:InvId:Password1
        expected = self._generate_signature(out_sum, inv_id, self.password1).lower()
        
        # Если есть shp_ параметры, нужно их учесть
        shp_params = sorted([(k, v) for k, v in data.items() if k.startswith('shp_')])
        if shp_params:
            sig_parts = [out_sum, inv_id]
            for key, value in shp_params:
                sig_parts.append(f"{key}={value}")
            sig_parts.append(self.password1)
            expected = self._generate_signature(*sig_parts).lower()
        
        return signature == expected