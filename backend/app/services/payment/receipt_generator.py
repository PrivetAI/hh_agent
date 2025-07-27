import hashlib
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote, urlencode
from ...core.config import settings

logger = logging.getLogger(__name__)

class ReceiptGenerator:
    """Генерация и форматирование чека для Робокассы"""
    
    ALLOWED_SNO = {
        "osn": "общая СН",
        "usn_income": "упрощенная СН (доходы)",
        "usn_income_outcome": "упрощенная СН (доходы минус расходы)",
        "envd": "единый налог на вмененный доход",
        "esn": "единый сельскохозяйственный налог",
        "patent": "патентная СН"
    }
    
    ALLOWED_TAX = {
        "none": "без НДС",
        "vat0": "НДС по ставке 0%",
        "vat10": "НДС по ставке 10%",
        "vat110": "НДС по расчетной ставке 10/110",
        "vat20": "НДС по ставке 20%",
        "vat120": "НДС по расчетной ставке 20/120"
    }
    
    ALLOWED_PAYMENT_METHOD = {
        "full_prepayment": "предоплата 100%",
        "prepayment": "предоплата",
        "advance": "аванс",
        "full_payment": "полный расчет",
        "partial_payment": "частичный расчет и кредит",
        "credit": "передача в кредит",
        "credit_payment": "оплата кредита"
    }
    
    ALLOWED_PAYMENT_OBJECT = {
        "commodity": "товар",
        "excise": "подакцизный товар",
        "job": "работа",
        "service": "услуга",
        "gambling_bet": "ставка азартной игры",
        "gambling_prize": "выигрыш азартной игры",
        "lottery": "лотерейный билет",
        "lottery_prize": "выигрыш лотереи",
        "intellectual_activity": "результаты интеллектуальной деятельности",
        "payment": "платеж",
        "agent_commission": "агентское вознаграждение",
        "composite": "составной предмет расчета",
        "another": "иной предмет расчета",
        "property_right": "имущественное право",
        "non-operating_gain": "внереализационный доход",
        "insurance_premium": "страховые взносы",
        "sales_tax": "торговый сбор",
        "resort_fee": "курортный сбор"
    }

    @staticmethod
    def validate_email(email: str) -> bool:
        """Проверка формата email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def generate_receipt(
        self,
        credits: int,
        amount: float,
        user_email: Optional[str] = None,
        sno: str = "usn_income",
        payment_method: str = "full_prepayment",
        payment_object: str = "service",
        tax: str = "none"
    ) -> Dict[str, Any]:
        """Генерация чека с валидацией"""
        if sno not in self.ALLOWED_SNO:
            raise ValueError(f"Недопустимая система налогообложения: {sno}")
        if tax not in self.ALLOWED_TAX:
            raise ValueError(f"Недопустимая ставка НДС: {tax}")
        if payment_method not in self.ALLOWED_PAYMENT_METHOD:
            raise ValueError(f"Недопустимый способ расчета: {payment_method}")
        if payment_object not in self.ALLOWED_PAYMENT_OBJECT:
            raise ValueError(f"Недопустимый предмет расчета: {payment_object}")

        item_name = f"Токены для генерации сопроводительных писем({credits} шт.)"
        receipt = {
            "sno": sno,
            "items": [
                {
                    "name": item_name,
                    "quantity": 1,
                    "sum": round(amount, 2),
                    "payment_method": payment_method,
                    "payment_object": payment_object,
                    "tax": tax
                }
            ]
        }
        if user_email and self.validate_email(user_email):
            receipt["customerContact"] = user_email
        logger.info(f"Сгенерирован чек: {receipt}")
        return receipt

    def format_receipt(self, receipt: Dict[str, Any]) -> str:
        """Форматирование чека в JSON для Робокассы"""
        receipt_copy = json.loads(json.dumps(receipt))
        for item in receipt_copy.get("items", []):
            if "sum" in item:
                item["sum"] = round(float(item["sum"]), 2)
            if "quantity" in item:
                qty = float(item["quantity"])
                item["quantity"] = int(qty) if qty == int(qty) else round(qty, 3)
            if "sum" in item and "quantity" in item and item["quantity"] != 0:
                item["price"] = round(item["sum"] / item["quantity"], 2)
        receipt_json = json.dumps(receipt_copy, ensure_ascii=False, separators=(',', ':'))
        logger.info(f"Отформатированный чек: {receipt_json}")
        return receipt_json
