import hashlib
import json
from typing import Dict, Any, Optional
from urllib.parse import urlencode, quote
from ...core.config import settings

class RobokassaPaymentService:
    def __init__(self):
        self.merchant_login = settings.ROBOKASSA_MERCHANT_LOGIN
        self.test_mode = settings.ROBOKASSA_TEST_MODE
        
        # Используем один URL для всех режимов
        self.base_url = "https://auth.robokassa.ru/Merchant/Index.aspx"

        if self.test_mode:
            self.password1 = settings.ROBOKASSA_TEST_PASSWORD_1
            self.password2 = settings.ROBOKASSA_TEST_PASSWORD_2
            print(f"DEBUG: Using TEST mode with merchant: {self.merchant_login}")
        else:
            self.password1 = settings.ROBOKASSA_PASSWORD_1
            self.password2 = settings.ROBOKASSA_PASSWORD_2
            print(f"DEBUG: Using PROD mode with merchant: {self.merchant_login}")
        
        # Проверяем что пароли не пустые
        if not self.password1 or not self.password2:
            raise ValueError(f"Robokassa passwords are not configured for {'TEST' if self.test_mode else 'PROD'} mode")

    def _generate_signature(self, *args) -> str:
        """
        Generate MD5 signature by concatenating all args with ':'
        and hashing the resulting string.
        """
        signature_string = ":".join(str(arg) for arg in args)
        print(f"DEBUG: Signature string: {signature_string}")
        return hashlib.md5(signature_string.encode('utf-8')).hexdigest()

    def create_payment_link(
        self,
        payment_id: int,
        amount: float,
        description: str,
        user_email: str = None,
        receipt_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build a Robokassa payment link, including optional fiscal receipt data.
        """
        out_sum = f"{amount:.2f}"
        inv_id = str(payment_id)

        # Base parameters
        params: Dict[str, Any] = {
            "MerchantLogin": self.merchant_login,
            "OutSum": out_sum,
            "InvId": inv_id,
            "Description": description,
            "Culture": "ru",
            "Encoding": "utf-8",
        }
        
        if user_email:
            params["Email"] = user_email

        # Handle fiscal Receipt if provided
        receipt_json = None
        # ВРЕМЕННО ОТКЛЮЧАЕМ ЧЕКИ ДЛЯ ТЕСТИРОВАНИЯ
        # if receipt_data:
        #     # JSON для подписи (компактный формат, без пробелов)
        #     receipt_json = json.dumps(receipt_data, ensure_ascii=False, separators=(',', ':'))
        #     params["Receipt"] = receipt_json
        #     print(f"DEBUG: Receipt JSON: {receipt_json}")

        # Собираем дополнительные параметры (shp_) в алфавитном порядке
        shp_params = {}
        for key, value in params.items():
            if key.startswith('shp_'):
                shp_params[key] = value

        # Build signature: MerchantLogin:OutSum:InvId[:ReceiptJSON][:shp_params]:Password1
        sig_parts = [self.merchant_login, out_sum, inv_id]
        
        # ВРЕМЕННО ОТКЛЮЧЕНО - Добавляем Receipt в подпись, если есть
        # if receipt_json:
        #     sig_parts.append(receipt_json)
            
        # Добавляем shp_ параметры в алфавитном порядке
        if shp_params:
            for key in sorted(shp_params.keys()):
                sig_parts.append(f"{key}={shp_params[key]}")
        
        # КРИТИЧНО: Добавляем пароль в конец
        sig_parts.append(self.password1)
        
        print(f"DEBUG: Signature parts: {sig_parts}")
        
        signature = self._generate_signature(*sig_parts)
        params["SignatureValue"] = signature
        print(f"DEBUG: Generated signature: {signature}")

        # Добавляем IsTest только ПОСЛЕ формирования подписи
        if self.test_mode:
            params["IsTest"] = "1"
            print(f"DEBUG: Test mode enabled")

        # ПРОВЕРЯЕМ что пароль не пустой (дополнительная проверка)
        if not self.password1:
            print(f"ERROR: Password1 is empty! Check your {'TEST' if self.test_mode else 'PROD'} settings.")
            raise ValueError("Password1 is not configured")
        
        print(f"DEBUG: Using password1: {self.password1[:10]}...")  # Показываем только первые 10 символов

        # Construct the final URL с правильным кодированием
        query_params = []
        for key, value in params.items():
            encoded_key = quote(str(key), safe='')
            encoded_value = quote(str(value), safe='')
            query_params.append(f"{encoded_key}={encoded_value}")
        
        final_url = f"{self.base_url}?{'&'.join(query_params)}"
        print(f"DEBUG: Final URL: {final_url}")
        
        return final_url

    def verify_success_url(self, data: Dict[str, Any]) -> bool:
        """
        Verify the signature from the success redirect.
        Uses Password1 in signature: OutSum:InvId[:shp_params]:Password1
        """
        out_sum = data.get("OutSum")
        inv_id = data.get("InvId")
        signature = data.get("SignatureValue", "").lower()
        
        if not all([out_sum, inv_id, signature]):
            print(f"DEBUG: Missing required fields for success verification")
            return False
        
        # Собираем shp_ параметры в алфавитном порядке
        shp_params = {}
        for key, value in data.items():
            if key.startswith('shp_'):
                shp_params[key] = value
        
        sig_parts = [out_sum, inv_id]
        
        # Добавляем shp_ параметры в алфавитном порядке
        if shp_params:
            for key in sorted(shp_params.keys()):
                sig_parts.append(f"{key}={shp_params[key]}")
        
        sig_parts.append(self.password1)
        
        expected = self._generate_signature(*sig_parts).lower()
        print(f"DEBUG: Success URL - Expected: {expected}, Received: {signature}")
        
        return signature == expected

    def verify_payment_result(self, data: Dict[str, Any]) -> bool:
        """
        Verify the signature in the payment result notification.
        Uses Password2 in signature: OutSum:InvId[:shp_params]:Password2
        """
        out_sum = data.get("OutSum")
        inv_id = data.get("InvId")
        signature = data.get("SignatureValue", "").lower()
        
        if not all([out_sum, inv_id, signature]):
            print(f"DEBUG: Missing required fields for result verification")
            return False
        
        # Собираем shp_ параметры в алфавитном порядке
        shp_params = {}
        for key, value in data.items():
            if key.startswith('shp_'):
                shp_params[key] = value
        
        sig_parts = [out_sum, inv_id]
        
        # Добавляем shp_ параметры в алфавитном порядке
        if shp_params:
            for key in sorted(shp_params.keys()):
                sig_parts.append(f"{key}={shp_params[key]}")
        
        sig_parts.append(self.password2)
        
        expected = self._generate_signature(*sig_parts).lower()
        print(f"DEBUG: Payment result - Expected: {expected}, Received: {signature}")
        
        return signature == expected