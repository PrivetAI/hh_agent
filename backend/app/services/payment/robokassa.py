import hashlib
import json
from typing import Dict, Any, Optional
from urllib.parse import urlencode, quote
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
            self.base_url = "https://robokassa.ru/Merchant/Index.aspx"

    def _generate_signature(self, *args) -> str:
        """Generate MD5 signature for Robokassa"""
        signature_string = ":".join(str(arg) for arg in args)
        return hashlib.md5(signature_string.encode()).hexdigest()

    def create_payment_link(
        self,
        payment_id: int,  # Изменено с UUID на int
        amount: float,
        description: str,
        user_email: str = None,
        receipt_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create payment link for Robokassa with receipt data"""
        out_sum = f"{amount:.2f}"
        inv_id = str(payment_id)  # Теперь это просто числовое значение

        # Базовые параметры для подписи
        signature_params = [self.merchant_login, out_sum, inv_id, self.password1]

        # Формируем параметры
        params = {
            "MerchantLogin": self.merchant_login,
            "OutSum": out_sum,
            "InvId": inv_id,
            "Description": description,
            "Culture": "ru",
            "Encoding": "utf-8",
        }

        # Добавляем email если передан
        if user_email:
            params["Email"] = user_email

        # Добавляем флаг тестового режима
        if self.test_mode:
            params["IsTest"] = "1"

        # Добавляем данные для фискализации если есть
        if receipt_data:
            receipt_json = json.dumps(receipt_data, ensure_ascii=False)
            params["Receipt"] = receipt_json

        # Генерируем подпись
        signature = self._generate_signature(*signature_params)
        params["SignatureValue"] = signature

        # Формируем URL
        return f"{self.base_url}?{urlencode(params)}"

    def verify_success_url(self, data: Dict[str, Any]) -> bool:
        """Verify success URL signature from Robokassa

        Success URL format: OutSum:InvId:Password1
        """
        try:
            out_sum = data.get("OutSum")
            inv_id = data.get("InvId")
            signature = data.get("SignatureValue", "").upper()  # Исправлена опечатка

            if not all([out_sum, inv_id, signature]):
                return False

            # Для Success URL используется password1
            expected_signature = self._generate_signature(
                out_sum, inv_id, self.password1
            ).upper()

            return signature == expected_signature
        except Exception as e:
            print(f"Error verifying Robokassa success signature: {e}")
            return False

    def verify_payment_result(self, data: Dict[str, Any]) -> bool:
        """Verify payment result from Robokassa

        Result URL format: OutSum:InvId:Password2
        """
        try:
            out_sum = data.get("OutSum")
            inv_id = data.get("InvId")
            signature = data.get("SignatureValue", "").upper()

            if not all([out_sum, inv_id, signature]):
                return False

            # Генерируем ожидаемую подпись
            expected_signature = self._generate_signature(
                out_sum, inv_id, self.password2
            ).upper()

            return signature == expected_signature
        except Exception as e:
            print(f"Error verifying Robokassa signature: {e}")
            return False
