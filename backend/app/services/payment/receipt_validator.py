"""
Receipt validator and generator for Robokassa fiscalization
According to 54-FZ requirements
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
import re


class ReceiptValidator:
    """Validates and generates receipts for Robokassa fiscalization"""
    
    # Допустимые системы налогообложения
    ALLOWED_SNO = {
        "osn": "общая СН",
        "usn_income": "упрощенная СН (доходы)",
        "usn_income_outcome": "упрощенная СН (доходы минус расходы)",
        "envd": "единый налог на вмененный доход",
        "esn": "единый сельскохозяйственный налог",
        "patent": "патентная СН"
    }
    
    # Допустимые ставки НДС
    ALLOWED_TAX = {
        "none": "без НДС",
        "vat0": "НДС по ставке 0%",
        "vat10": "НДС по ставке 10%",
        "vat110": "НДС по расчетной ставке 10/110",
        "vat20": "НДС по ставке 20%",
        "vat120": "НДС по расчетной ставке 20/120"
    }
    
    # Допустимые способы расчета
    ALLOWED_PAYMENT_METHOD = {
        "full_prepayment": "предоплата 100%",
        "prepayment": "предоплата",
        "advance": "аванс",
        "full_payment": "полный расчет",
        "partial_payment": "частичный расчет и кредит",
        "credit": "передача в кредит",
        "credit_payment": "оплата кредита"
    }
    
    # Допустимые признаки предмета расчета
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
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone format (+79001234567)"""
        pattern = r'^\+7\d{10}$'
        return bool(re.match(pattern, phone))
    
    @classmethod
    def validate_receipt(cls, receipt: Dict[str, Any]) -> List[str]:
        """
        Validate receipt data according to Robokassa requirements
        Returns list of errors (empty if valid)
        """
        errors = []
        
        # Проверка системы налогообложения
        if "sno" not in receipt:
            errors.append("Отсутствует система налогообложения (sno)")
        elif receipt["sno"] not in cls.ALLOWED_SNO:
            errors.append(f"Недопустимая система налогообложения: {receipt['sno']}")
        
        # Проверка позиций
        if "items" not in receipt or not receipt["items"]:
            errors.append("Отсутствуют позиции чека (items)")
        else:
            for i, item in enumerate(receipt["items"]):
                item_errors = cls._validate_item(item, i)
                errors.extend(item_errors)
        
        # Проверка контакта покупателя
        if "customerContact" in receipt:
            contact = receipt["customerContact"]
            if "@" in contact and not cls.validate_email(contact):
                errors.append(f"Некорректный email покупателя: {contact}")
            elif contact.startswith("+") and not cls.validate_phone(contact):
                errors.append(f"Некорректный телефон покупателя: {contact}")
        
        return errors
    
    @classmethod
    def _validate_item(cls, item: Dict[str, Any], index: int) -> List[str]:
        """Validate single receipt item"""
        errors = []
        prefix = f"Позиция {index + 1}: "
        
        # Обязательные поля
        if "name" not in item or not item["name"]:
            errors.append(f"{prefix}отсутствует наименование")
        elif len(item["name"]) > 128:
            errors.append(f"{prefix}наименование превышает 128 символов")
        
        if "quantity" not in item:
            errors.append(f"{prefix}отсутствует количество")
        elif not isinstance(item["quantity"], (int, float)) or item["quantity"] <= 0:
            errors.append(f"{prefix}некорректное количество")
        
        if "sum" not in item:
            errors.append(f"{prefix}отсутствует сумма")
        elif not isinstance(item["sum"], (int, float)) or item["sum"] < 0:
            errors.append(f"{prefix}некорректная сумма")
        
        # НДС
        if "tax" not in item:
            errors.append(f"{prefix}отсутствует ставка НДС")
        elif item["tax"] not in cls.ALLOWED_TAX:
            errors.append(f"{prefix}недопустимая ставка НДС: {item['tax']}")
        
        # Способ расчета
        if "payment_method" not in item:
            errors.append(f"{prefix}отсутствует способ расчета")
        elif item["payment_method"] not in cls.ALLOWED_PAYMENT_METHOD:
            errors.append(f"{prefix}недопустимый способ расчета: {item['payment_method']}")
        
        # Предмет расчета
        if "payment_object" not in item:
            errors.append(f"{prefix}отсутствует предмет расчета")
        elif item["payment_object"] not in cls.ALLOWED_PAYMENT_OBJECT:
            errors.append(f"{prefix}недопустимый предмет расчета: {item['payment_object']}")
        
        return errors
    
    @staticmethod
    def generate_receipt(
        credits: int,
        amount: float,
        user_email: Optional[str] = None,
        sno: str = "usn_income"
    ) -> Dict[str, Any]:
        """
        Generate valid receipt for credit package
        
        Args:
            package_name: Package identifier
            credits: Number of credits
            amount: Total amount
            user_email: Customer email (optional)
            sno: Tax system (default: usn_income)
        """
        receipt = {
            "sno": sno,
            "items": [
                {
                    "name": f"Токены для генерации ({credits} шт.)",
                    "quantity": 1.0,
                    "sum": float(amount),
                    "payment_method": "full_prepayment",
                    "payment_object": "service",
                    "tax": "none"
                }
            ]
        }
        
        # Добавляем контакт покупателя если есть
        if user_email and ReceiptValidator.validate_email(user_email):
            receipt["customerContact"] = user_email
            
        return receipt