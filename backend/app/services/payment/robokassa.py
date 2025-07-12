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
            logger.warning(f"Robokassa passwords not fully configured for {'TEST' if self.test_mode else 'PROD'} mode")

    def _generate_signature(self, *args) -> str:
        """Generate MD5 signature from args"""
        signature_string = ":".join(str(arg) for arg in args if arg is not None)
        return hashlib.md5(signature_string.encode("utf-8")).hexdigest()

    def _format_amount(self, amount: float) -> str:
        """Format amount for Robokassa (e.g., 149.00)"""
        return f"{amount:.2f}"

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
            # Test mode - simple signature without receipt
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
                # Log original receipt data
                logger.info(f"Original receipt data: {json.dumps(receipt_data, ensure_ascii=False)}")
                
                # ВАЖНО: Убедимся что в чеке правильный формат чисел
                receipt_copy = json.loads(json.dumps(receipt_data))
                
                # Форматируем числа в items
                if "items" in receipt_copy:
                    for item in receipt_copy["items"]:
                        # Логируем название товара
                        logger.info(f"Item name in receipt: {item.get('name', 'NO NAME')}")
                        
                        # sum должен быть числом с точкой
                        if "sum" in item:
                            item["sum"] = float(item["sum"])
                        # quantity должен быть числом
                        if "quantity" in item:
                            qty = float(item["quantity"])
                            # Если целое число, храним как int
                            if qty == int(qty):
                                item["quantity"] = int(qty)
                            else:
                                item["quantity"] = qty
                
                # Создаем JSON строку БЕЗ пробелов для подписи
                receipt_json = json.dumps(receipt_copy, ensure_ascii=False, separators=(',', ':'))
                
                logger.info(f"Receipt JSON for signature: {receipt_json}")
                logger.info(f"Receipt JSON length: {len(receipt_json)}")
                
                # Вычисляем подпись с НЕ закодированным чеком
                # Порядок: MerchantLogin:OutSum:InvId:Receipt:Password1
                sig_components = [
                    self.merchant_login,
                    out_sum,
                    inv_id,
                    receipt_json,
                    self.password1
                ]
                
                sig_string = ":".join(sig_components)
                logger.info(f"Signature string length: {len(sig_string)}")
                logger.info(f"Signature string: {sig_string[:200]}...") # Показываем только начало
                
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
                
                # ВАЖНО: Receipt добавляем в параметры как есть (urlencode сделает кодирование)
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

        # Генерируем URL (urlencode автоматически закодирует Receipt)
        url = f"{self.base_url}?{urlencode(params, quote_via=quote_plus)}"
        
        logger.info(f"Payment URL created, length: {len(url)} chars")
        logger.debug(f"Final URL (first 200 chars): {url[:200]}...")
        
        # Дополнительная отладка параметров
        logger.debug(f"Final params keys: {list(params.keys())}")
        for key, value in params.items():
            if key != "Receipt":
                logger.debug(f"Param {key}: {value}")
            else:
                logger.debug(f"Param Receipt length: {len(value)}")
        
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
        if isinstance(out_sum, str) and '.' not in out_sum:
            out_sum = f"{out_sum}.00"

        # Build signature components
        # Order for result: OutSum:InvId:Receipt:Password2
        sig_components = [out_sum, inv_id]
        
        # Add Receipt if present
        if data.get("Receipt"):
            sig_components.append(data["Receipt"])
        
        # Add shp_ parameters in sorted order
        shp_params = sorted((k, v) for k, v in data.items() if k.startswith("shp_"))
        for key, value in shp_params:
            sig_components.append(f"{key}={value}")
        
        # Add password2
        sig_components.append(self.password2)
        
        # Calculate expected signature
        sig_string = ":".join(sig_components)
        expected = hashlib.md5(sig_string.encode("utf-8")).hexdigest().lower()
        
        match = received_sig == expected
        
        if not match:
            logger.warning(f"Payment result signature mismatch")
            logger.warning(f"Expected: {expected}")
            logger.warning(f"Received: {received_sig}")
            logger.debug(f"Signature string: {sig_string}")
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
        if isinstance(out_sum, str) and '.' not in out_sum:
            out_sum = f"{out_sum}.00"

        # Build signature components
        # Order for success: OutSum:InvId:Receipt:Password1
        sig_components = [out_sum, inv_id]
        
        # Add Receipt if present
        if data.get("Receipt"):
            sig_components.append(data["Receipt"])
        
        # Add shp_ parameters in sorted order
        shp_params = sorted((k, v) for k, v in data.items() if k.startswith("shp_"))
        for key, value in shp_params:
            sig_components.append(f"{key}={value}")
        
        # Add password1
        sig_components.append(self.password1)
        
        # Calculate expected signature
        sig_string = ":".join(sig_components)
        expected = hashlib.md5(sig_string.encode("utf-8")).hexdigest().lower()
        
        match = received_sig == expected
        
        if not match:
            logger.warning(f"Success URL signature mismatch")
            logger.warning(f"Expected: {expected}")
            logger.warning(f"Received: {received_sig}")
            logger.debug(f"Signature string: {sig_string}")
        else:
            logger.info("Success URL signature verified successfully")
            
        return match