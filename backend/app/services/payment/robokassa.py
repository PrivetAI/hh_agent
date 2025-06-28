import hashlib
from typing import Dict, Any
from urllib.parse import urlencode
from uuid import UUID

from ...core.config import settings


class RobokassaPaymentService:
    def __init__(self):
        self.merchant_login = settings.ROBOKASSA_MERCHANT_LOGIN
        self.test_mode = settings.ROBOKASSA_TEST_MODE
        
        # Выбираем пароли в зависимости от режима
        if self.test_mode:
            self.password1 = settings.ROBOKASSA_TEST_PASSWORD_1
            self.password2 = settings.ROBOKASSA_TEST_PASSWORD_2
            self.base_url = "https://auth.robokassa.ru/Merchant/Index.aspx"
        else:
            self.password1 = settings.ROBOKASSA_PASSWORD_1
            self.password2 = settings.ROBOKASSA_PASSWORD_2
            self.base_url = "https://auth.robokassa.ru/Merchant/Index.aspx"
    
    def _generate_signature(self, *args) -> str:
        """Generate MD5 signature for Robokassa"""
        signature_string = ":".join(str(arg) for arg in args)
        return hashlib.md5(signature_string.encode()).hexdigest()
    
    def create_payment_link(self, payment_id: UUID, amount: float, description: str) -> str:
        """Create payment link for Robokassa"""
        out_sum = f"{amount:.2f}"
        inv_id = str(payment_id)
        
        # Генерируем подпись
        signature = self._generate_signature(
            self.merchant_login,
            out_sum,
            inv_id,
            self.password1
        )
        
        # Формируем параметры
        params = {
            "MerchantLogin": self.merchant_login,
            "OutSum": out_sum,
            "InvId": inv_id,
            "Description": description,
            "SignatureValue": signature,
            "Culture": "ru",
            "Encoding": "utf-8"
        }
        
        # Добавляем флаг тестового режима
        if self.test_mode:
            params["IsTest"] = "1"
        
        # Формируем URL
        return f"{self.base_url}?{urlencode(params)}"
    
    def verify_payment_result(self, data: Dict[str, Any]) -> bool:
        """Verify payment result from Robokassa"""
        try:
            out_sum = data.get("OutSum")
            inv_id = data.get("InvId")
            signature = data.get("SignatureValue", "").upper()
            
            # Генерируем ожидаемую подпись
            expected_signature = self._generate_signature(
                out_sum,
                inv_id,
                self.password2
            ).upper()
            
            return signature == expected_signature
        except Exception as e:
            print(f"Error verifying Robokassa signature: {e}")
            return False
    
    def verify_success_url(self, data: Dict[str, Any]) -> bool:
        """Verify success URL signature from Robokassa"""
        try:
            out_sum = data.get("OutSum")
            inv_id = data.get("InvId")
            signature = data.get("SignatureValue", "").upper()
            
            # Для Success URL используется password1
            expected_signature = self._generate_signature(
                out_sum,
                inv_id,
                self.password1
            ).upper()
            
            return signature == expected_signature
        except Exception as e:
            print(f"Error verifying Robokassa success signature: {e}")
            return False