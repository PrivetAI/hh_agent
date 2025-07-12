import hashlib
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode, quote_plus, quote
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
            logger.info(f"Robokassa passwords not fully configured for {'TEST' if self.test_mode else 'PROD'} mode")

    def _generate_signature(self, *args) -> str:
        """Generate MD5 signature from args"""
        signature_string = ":".join(str(arg) for arg in args if arg is not None)
        return hashlib.md5(signature_string.encode("utf-8")).hexdigest()

    def _format_amount(self, amount: float) -> str:
        """Format amount for Robokassa (e.g., 149.00)"""
        return f"{amount:.2f}"

    def _format_receipt_for_robokassa(self, receipt_data: Dict[str, Any]) -> str:
        """Format receipt data according to Robokassa requirements"""
        receipt_copy = json.loads(json.dumps(receipt_data))
        
        # Форматируем items согласно требованиям Robokassa
        if "items" in receipt_copy:
            for item in receipt_copy["items"]:
                # sum должно быть числом с 2 знаками после запятой
                if "sum" in item:
                    item["sum"] = round(float(item["sum"]), 2)
                
                # quantity должно быть числом (целым если возможно)
                if "quantity" in item:
                    qty = float(item["quantity"])
                    if qty == int(qty):
                        item["quantity"] = int(qty)
                    else:
                        item["quantity"] = round(qty, 3)
                
                # price - цена за единицу (обязательно для новой версии API)
                if "sum" in item and "quantity" in item:
                    item["price"] = round(item["sum"] / item["quantity"], 2)
        
        # Создаем JSON строку БЕЗ пробелов и с русскими символами
        receipt_json = json.dumps(receipt_copy, ensure_ascii=False, separators=(',', ':'))
        
        return receipt_json

    def create_payment_link(
        self,
        payment_id: int,
        amount: float,
        description: str,
        user_email: str = None,
        receipt_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create payment link with proper receipt handling"""
        
        # Format amount
        out_sum = self._format_amount(amount)
        inv_id = str(payment_id)
        
        logger.info(f"Creating payment link in {'TEST' if self.test_mode else 'PRODUCTION'} mode")
        logger.info(f"Amount: {amount} -> OutSum: {out_sum}")
        logger.info(f"InvId: {inv_id}")
        logger.info(f"Description: {description}")

        if self.test_mode:
            # Test mode - простая подпись без чека
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
            # Production mode
            if receipt_data:
                # Форматируем чек согласно требованиям Robokassa
                receipt_json = self._format_receipt_for_robokassa(receipt_data)
                
                logger.info(f"Formatted receipt JSON: {receipt_json}")
                logger.info(f"Receipt JSON length: {len(receipt_json)}")
                
                # Вычисляем подпись
                # Порядок для создания платежа: MerchantLogin:OutSum:InvId:Receipt:Password1
                sig_components = [
                    self.merchant_login,
                    out_sum,
                    inv_id,
                    receipt_json,
                    self.password1
                ]
                
                sig_string = ":".join(sig_components)
                logger.info(f"Signature string length: {len(sig_string)}")
                
                sig = hashlib.md5(sig_string.encode("utf-8")).hexdigest()
                logger.info(f"Calculated signature: {sig}")
                
                # Формируем параметры
                params = {
                    "MerchantLogin": self.merchant_login,
                    "OutSum": out_sum,
                    "InvId": inv_id,
                    "Description": description,
                    "SignatureValue": sig,
                    "Culture": "ru",
                    "Encoding": "utf-8"
                }
                
                # Добавляем email если есть
                if user_email:
                    params["Email"] = user_email
                
                # Добавляем чек
                params["Receipt"] = receipt_json
                
            else:
                # Production без чека
                sig = self._generate_signature(self.merchant_login, out_sum, inv_id, self.password1)
                params = {
                    "MerchantLogin": self.merchant_login,
                    "OutSum": out_sum,
                    "InvId": inv_id,
                    "Description": description,
                    "SignatureValue": sig,
                    "Culture": "ru",
                    "Encoding": "utf-8"
                }
                if user_email:
                    params["Email"] = user_email

        # Генерируем URL
        # ВАЖНО: используем quote_plus для правильного кодирования
        url_params = []
        for key, value in params.items():
            if key == "Receipt":
                # Для чека используем специальное кодирование
                encoded_receipt = quote(value, safe='')
                url_params.append(f"{key}={encoded_receipt}")
            else:
                url_params.append(f"{key}={quote_plus(str(value))}")
        
        url = f"{self.base_url}?{'&'.join(url_params)}"
        
        logger.info(f"Payment URL created, length: {len(url)} chars")
        logger.info(f"Final URL (first 200 chars): {url[:200]}...")
        
        return url

    def verify_payment_result(self, data: Dict[str, Any]) -> bool:
        """Verify payment result signature (uses password2)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        received_sig = data.get("SignatureValue", "").lower()
        
        if not (out_sum and inv_id and received_sig):
            logger.error("Missing required parameters for payment result verification")
            return False

        # Format amount if needed
        if isinstance(out_sum, (int, float)):
            out_sum = self._format_amount(float(out_sum))
        elif isinstance(out_sum, str) and '.' not in out_sum:
            out_sum = f"{out_sum}.00"

        # Build signature components
        # Порядок для результата: OutSum:InvId:Receipt:Password2
        sig_components = [out_sum, inv_id]
        
        # Добавляем Receipt если присутствует
        if data.get("Receipt"):
            sig_components.append(data["Receipt"])
        
        # Добавляем shp_ параметры в отсортированном порядке
        shp_params = sorted((k, v) for k, v in data.items() if k.startswith("shp_"))
        for key, value in shp_params:
            sig_components.append(f"{key}={value}")
        
        # Добавляем password2
        sig_components.append(self.password2)
        
        # Вычисляем ожидаемую подпись
        sig_string = ":".join(sig_components)
        expected = hashlib.md5(sig_string.encode("utf-8")).hexdigest().lower()
        
        match = received_sig == expected
        
        if not match:
            logger.info(f"Payment result signature mismatch")
            logger.info(f"Expected: {expected}")
            logger.info(f"Received: {received_sig}")
            logger.info(f"Signature string: {sig_string}")
        else:
            logger.info("Payment result signature verified successfully")
            
        return match

    def verify_success_url(self, data: Dict[str, Any]) -> bool:
        """Verify success redirect signature (uses password1)"""
        out_sum = data.get("OutSum", "")
        inv_id = data.get("InvId", "")
        received_sig = data.get("SignatureValue", "").lower()
        
        if not (out_sum and inv_id and received_sig):
            logger.error("Missing required parameters for success URL verification")
            return False

        # Format amount if needed
        if isinstance(out_sum, (int, float)):
            out_sum = self._format_amount(float(out_sum))
        elif isinstance(out_sum, str) and '.' not in out_sum:
            out_sum = f"{out_sum}.00"

        # Build signature components
        # Порядок для success: OutSum:InvId:Receipt:Password1
        sig_components = [out_sum, inv_id]
        
        # Добавляем Receipt если присутствует
        if data.get("Receipt"):
            sig_components.append(data["Receipt"])
        
        # Добавляем shp_ параметры в отсортированном порядке
        shp_params = sorted((k, v) for k, v in data.items() if k.startswith("shp_"))
        for key, value in shp_params:
            sig_components.append(f"{key}={value}")
        
        # Добавляем password1
        sig_components.append(self.password1)
        
        # Вычисляем ожидаемую подпись
        sig_string = ":".join(sig_components)
        expected = hashlib.md5(sig_string.encode("utf-8")).hexdigest().lower()
        
        match = received_sig == expected
        
        if not match:
            logger.info(f"Success URL signature mismatch")
            logger.info(f"Expected: {expected}")
            logger.info(f"Received: {received_sig}")
            logger.info(f"Signature string: {sig_string}")
        else:
            logger.info("Success URL signature verified successfully")
            
        return match