import hashlib
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode, quote_plus, quote
from ...core.config import settings
from .receipt_generator import ReceiptGenerator
logger = logging.getLogger(__name__)

class RobokassaService:
    """Сервис для работы с Робокассой"""
    
    def __init__(self):
        self.merchant_login = settings.ROBOKASSA_MERCHANT_LOGIN
        self.base_url = "https://auth.robokassa.ru/Merchant/Index.aspx"  # Единый URL для теста и продакшена
        self.test_mode = settings.ROBOKASSA_TEST_MODE
        self.receipt_generator = ReceiptGenerator()

        if self.test_mode:
            self.password1 = settings.ROBOKASSA_TEST_PASSWORD_1
            self.password2 = settings.ROBOKASSA_TEST_PASSWORD_2
            logger.info("Робокасса инициализирована в тестовом режиме")
        else:
            self.password1 = settings.ROBOKASSA_PASSWORD_1
            self.password2 = settings.ROBOKASSA_PASSWORD_2
            logger.info("Робокасса инициализирована в рабочем режиме")

        if not self.password1 or not self.password2:
            logger.warning(f"Пароли Робокассы не полностью настроены для {'тестового' if self.test_mode else 'рабочего'} режима")

    def _generate_signature(self, *args) -> str:
        """Генерация MD5 подписи"""
        signature_string = ":".join(str(arg) for arg in args if arg is not None)
        return hashlib.md5(signature_string.encode("utf-8")).hexdigest()

    def _format_amount(self, amount: float) -> str:
        """Форматирование суммы (например, 149.00)"""
        return f"{amount:.2f}"

    def create_payment_link(
        self,
        payment_id: int,
        amount: float,
        description: str,
        user_email: Optional[str] = None,
        receipt_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Создание ссылки на оплату"""
        out_sum = self._format_amount(amount)
        inv_id = str(payment_id)

        logger.info(f"Создание ссылки на оплату в {'тестовом' if self.test_mode else 'рабочем'} режиме")
        logger.info(f"Сумма: {amount} -> OutSum: {out_sum}")
        logger.info(f"InvId: {inv_id}")
        logger.info(f"Описание: {description}")

        params = {
            "MerchantLogin": self.merchant_login,
            "OutSum": out_sum,
            "InvId": inv_id,
            "Description": description,
            "Culture": "ru",
            "Encoding": "utf-8",
        }

        if self.test_mode:
            params["IsTest"] = "1"

        if receipt_data:
            receipt_json = self.receipt_generator.format_receipt(receipt_data)
            params["Receipt"] = receipt_json
            sig = self._generate_signature(self.merchant_login, out_sum, inv_id, receipt_json, self.password1)
        else:
            sig = self._generate_signature(self.merchant_login, out_sum, inv_id, self.password1)

        params["SignatureValue"] = sig
        if user_email:
            params["Email"] = user_email

        url_params = urlencode(params, quote_via=lambda x, *args: quote(x, safe=''))
        url = f"{self.base_url}?{url_params}"
        logger.info(f"Создана ссылка на оплату, длина: {len(url)} символов")
        return url

    def verify_payment_result(self, data: Dict[str, Any]) -> bool:
        """Проверка подписи результата оплаты (использует password2)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        received_sig = data.get("SignatureValue", "").lower()

        if not (out_sum and inv_id and received_sig):
            logger.error("Отсутствуют обязательные параметры для проверки результата оплаты")
            return False

        sig_components = [out_sum, inv_id]
        if "Receipt" in data:
            sig_components.append(data["Receipt"])
        sig_components.append(self.password2)
        expected = self._generate_signature(*sig_components).lower()

        match = received_sig == expected
        if not match:
            logger.info(f"Подпись результата оплаты не совпадает")
            logger.info(f"Ожидаемая: {expected}")
            logger.info(f"Полученная: {received_sig}")
        else:
            logger.info("Подпись результата оплаты успешно проверена")
        return match

    def verify_success_url(self, data: Dict[str, Any]) -> bool:
        """Проверка подписи URL успешной оплаты (использует password1)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        received_sig = data.get("SignatureValue", "").lower()

        if not (out_sum and inv_id and received_sig):
            logger.error("Отсутствуют обязательные параметры для проверки URL успешной оплаты")
            return False

        sig_components = [out_sum, inv_id]
        if "Receipt" in data:
            sig_components.append(data["Receipt"])
        sig_components.append(self.password1)
        expected = self._generate_signature(*sig_components).lower()

        match = received_sig == expected
        if not match:
            logger.info(f"Подпись URL успешной оплаты не совпадает")
            logger.info(f"Ожидаемая: {expected}")
            logger.info(f"Полученная: {received_sig}")
        else:
            logger.info("Подпись URL успешной оплаты успешно проверена")
        return match

