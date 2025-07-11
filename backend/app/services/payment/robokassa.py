import hashlib
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode, quote_plus
from ...core.config import settings

logger = logging.getLogger(__name__)


class RobokassaPaymentService:
    def __init__(self):
        self.merchant_login = settings.ROBOKASSA_MERCHANT_LOGIN
        self.base_url = "https://auth.robokassa.ru/Merchant/Index.aspx"
        self.test_mode = settings.ROBOKASSA_TEST_MODE

        if self.test_mode:
            self.password1 = settings.ROBOKASSA_TEST_PASSWORD_1 or "BCd7XYGZ42m4cbeHX6be"
            self.password2 = settings.ROBOKASSA_TEST_PASSWORD_2 or "pjXW77PQV28NP2glvHfp"
            logger.info("Robokassa initialized in TEST mode")
        else:
            self.password1 = settings.ROBOKASSA_PASSWORD_1
            self.password2 = settings.ROBOKASSA_PASSWORD_2
            logger.info("Robokassa initialized in PRODUCTION mode")

        if not self.password1 or not self.password2:
            logger.warning(f"Robokassa passwords not fully configured for {'TEST' if self.test_mode else 'PROD'} mode")
            if not self.password1:
                self.password1 = "dummy_password1"
            if not self.password2:
                self.password2 = "dummy_password2"

    def _generate_signature(self, *args) -> str:
        signature_string = ":".join(str(arg) for arg in args if arg is not None)
        logger.debug(f"Signature string: {signature_string}")
        return hashlib.md5(signature_string.encode("utf-8")).hexdigest()

    def create_payment_link(
        self,
        payment_id: int,
        amount: float,
        description: str,
        user_email: str = None,
        receipt_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        out_sum = f"{amount:.2f}"
        inv_id = str(payment_id)
        logger.info(f"Creating payment link in {'TEST' if self.test_mode else 'PRODUCTION'} mode")

        if self.test_mode:
            sig = self._generate_signature(self.merchant_login, out_sum, inv_id, self.password1)
            params = {
                "MerchantLogin": self.merchant_login,
                "OutSum": out_sum,
                "InvId": inv_id,
                "SignatureValue": sig,
                "IsTest": "1",
            }
            if description:
                params["Description"] = description

        else:
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

            if receipt_data:
                # Формируем JSON чека с компактными разделителями
                receipt_json = json.dumps(receipt_data, ensure_ascii=False, separators=(",", ":"))
                logger.info(f"Receipt JSON: {receipt_json}")  # Логируем точное значение receipt_json

                # Формируем строку для подписи
                sig_str = f"{self.merchant_login}:{out_sum}:{inv_id}:{receipt_json}:{self.password1}"
                logger.debug(f"Signature string for MD5: {sig_str}")
                sig = hashlib.md5(sig_str.encode("utf-8")).hexdigest()
                logger.debug(f"Calculated signature: {sig}")

                # Добавляем receipt_json в параметры
                params["Receipt"] = receipt_json
            else:
                sig = self._generate_signature(self.merchant_login, out_sum, inv_id, self.password1)

            params["SignatureValue"] = sig

        # Генерируем URL
        url = f"{self.base_url}?{urlencode(params, quote_via=quote_plus)}"
        logger.info(f"Payment URL created, length: {len(url)} chars")
        return url

    def verify_payment_result(self, data: Dict[str, Any]) -> bool:
        """Проверяем подпись результата платежа (используем password2)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        received_sig = data.get("SignatureValue", "").lower()
        if not (out_sum and inv_id and received_sig):
            return False

        # Собираем параметры shps и Receipt
        shp_parts = sorted((k, v) for k, v in data.items() if k.startswith("shp_"))
        parts = [out_sum, inv_id]
        if data.get("Receipt"):
            parts.append(data["Receipt"])
        parts += [f"{k}={v}" for k, v in shp_parts]
        parts.append(self.password2)

        expected = hashlib.md5(":".join(parts).encode("utf-8")).hexdigest().lower()
        match = received_sig == expected
        if not match:
            logger.warning(f"Payment result signature mismatch: expected {expected}, got {received_sig}")
        return match

    def verify_success_url(self, data: Dict[str, Any]) -> bool:
        """Проверяем подпись success-редиректа (используем password1)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        received_sig = data.get("SignatureValue", "").lower()
        if not (out_sum and inv_id and received_sig):
            return False

        shp_parts = sorted((k, v) for k, v in data.items() if k.startswith("shp_"))
        parts = [out_sum, inv_id]
        if data.get("Receipt"):
            parts.append(data["Receipt"])
        parts += [f"{k}={v}" for k, v in shp_parts]
        parts.append(self.password1)

        expected = hashlib.md5(":".join(parts).encode("utf-8")).hexdigest().lower()
        return received_sig == expected
