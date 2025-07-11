import hashlib
import json
import logging
import os
from typing import Dict, Any, Optional
from urllib.parse import quote, urlencode, quote_plus
from ...core.config import settings

logger = logging.getLogger(__name__)

class RobokassaPaymentService:
    def __init__(self):
        self.merchant_login = settings.ROBOKASSA_MERCHANT_LOGIN
        self.base_url = "https://auth.robokassa.ru/Merchant/Index.aspx"
        
        self.test_mode = settings.ROBOKASSA_TEST_MODE
        
        logger.info(f"Initializing Robokassa: test_mode={self.test_mode}, merchant={self.merchant_login}")
        if self.test_mode:
            self.password1 = settings.ROBOKASSA_TEST_PASSWORD_1 or "BCd7XYGZ42m4cbeHX6be"
            self.password2 = settings.ROBOKASSA_TEST_PASSWORD_2 or "pjXW77PQV28NP2glvHfp"
            logger.info(f"Robokassa initialized in TEST mode")
        else:
            self.password1 = settings.ROBOKASSA_PASSWORD_1
            self.password2 = settings.ROBOKASSA_PASSWORD_2
            logger.info(f"Robokassa initialized in PRODUCTION mode")
        
        if not self.password1 or not self.password2:
            logger.warning(f"Robokassa passwords not fully configured for {'TEST' if self.test_mode else 'PROD'} mode")
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

    def _clean_receipt_data(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean receipt data from problematic characters"""
        cleaned_data = receipt_data.copy()
        
        # Очищаем названия товаров от экранированных кавычек и других проблемных символов
        if 'items' in cleaned_data:
            for item in cleaned_data['items']:
                if 'name' in item:
                    # Убираем экранированные кавычки и заменяем на обычные
                    name = item['name']
                    name = name.replace('\\"', '"')  # Убираем экранирование
                    name = name.replace('"', '')     # Убираем все кавычки
                    item['name'] = name
                    
        return cleaned_data

    def create_payment_link(
        self,
        payment_id: int,
        amount: float,
        description: str,
        user_email: str = None,
        receipt_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create payment link with optional receipt for fiscalization"""
        out_sum = f"{amount:.2f}"
        inv_id = str(payment_id)

        logger.info(f"Creating payment link in {'TEST' if self.test_mode else 'PRODUCTION'} mode")
        
        if self.test_mode:
            # В тестовом режиме чеки не поддерживаются
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
            
            if description:
                params["Description"] = description
                
        else:
            # Production mode with receipt support
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
            
            # Формируем подпись
            if receipt_data:
                # Очищаем чек от проблемных символов
                cleaned_receipt = self._clean_receipt_data(receipt_data)
                
                # Сериализуем чек в JSON без пробелов
                receipt_json = json.dumps(cleaned_receipt, ensure_ascii=False, separators=(',', ':'))
                
                # Подпись с чеком: MerchantLogin:OutSum:InvId:Receipt:Password1
                signature = self._generate_signature(
                    self.merchant_login,
                    out_sum,
                    inv_id,
                    receipt_json,  # JSON чека в незакодированном виде для подписи
                    self.password1
                )
                
                # Для параметра Receipt используем обычную строку JSON
                params["Receipt"] = receipt_json
                
                logger.info(f"Receipt added to payment, length: {len(receipt_json)} chars")
                logger.debug(f"Receipt JSON: {receipt_json}")
            else:
                # Подпись без чека: MerchantLogin:OutSum:InvId:Password1
                signature = self._generate_signature(
                    self.merchant_login,
                    out_sum,
                    inv_id,
                    self.password1
                )
            
            params["SignatureValue"] = signature
    
        logger.info(f"Creating payment URL with params: {list(params.keys())}")
        
        # Используем urlencode с правильными параметрами
        url = f"{self.base_url}?{urlencode(params, quote_via=quote_plus)}"
            
        logger.info(f"Payment URL created, length: {len(url)} chars")
        
        return url

    def verify_payment_result(self, data: Dict[str, Any]) -> bool:
        """Verify payment result signature (uses Password2)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        signature = data.get("SignatureValue", "").lower()
        
        if not all([out_sum, inv_id, signature]):
            logger.warning("Missing required fields for payment verification")
            return False
        
        # Базовая подпись без дополнительных параметров
        expected = self._generate_signature(out_sum, inv_id, self.password2).lower()
        
        # Проверяем наличие дополнительных параметров (включая Receipt)
        shp_params = sorted([(k, v) for k, v in data.items() if k.startswith('shp_')])
        receipt = data.get('Receipt')
        
        if shp_params or receipt:
            sig_parts = [out_sum, inv_id]
            
            # Добавляем Receipt если есть (должен быть первым после основных параметров)
            if receipt:
                sig_parts.append(receipt)
            
            # Добавляем shp_ параметры
            for key, value in shp_params:
                sig_parts.append(f"{key}={value}")
                
            sig_parts.append(self.password2)
            expected = self._generate_signature(*sig_parts).lower()
        
        result = signature == expected
        
        if not result:
            logger.warning(f"Signature mismatch. Expected: {expected}, Got: {signature}")
            logger.warning(f"Data: OutSum={out_sum}, InvId={inv_id}, Receipt={'present' if receipt else 'absent'}")
        
        return result

    def verify_success_url(self, data: Dict[str, Any]) -> bool:
        """Verify success URL signature (uses Password1)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        signature = data.get("SignatureValue", "").lower()
        
        if not all([out_sum, inv_id, signature]):
            return False
        
        # Базовая подпись без дополнительных параметров
        expected = self._generate_signature(out_sum, inv_id, self.password1).lower()
        
        # Проверяем наличие дополнительных параметров (включая Receipt)
        shp_params = sorted([(k, v) for k, v in data.items() if k.startswith('shp_')])
        receipt = data.get('Receipt')
        
        if shp_params or receipt:
            sig_parts = [out_sum, inv_id]
            
            # Добавляем Receipt если есть
            if receipt:
                sig_parts.append(receipt)
            
            # Добавляем shp_ параметры
            for key, value in shp_params:
                sig_parts.append(f"{key}={value}")
                
            sig_parts.append(self.password1)
            expected = self._generate_signature(*sig_parts).lower()
        
        return signature == expected