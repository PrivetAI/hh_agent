import hashlib
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from uuid import UUID
import logging

from ...core.config import settings

logger = logging.getLogger(__name__)

class RobokassaPaymentService:
    def __init__(self):
        self.merchant_login = settings.ROBOKASSA_MERCHANT_LOGIN
        self.test_mode = settings.ROBOKASSA_TEST_MODE
        
        # Choose passwords based on mode
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
        # Filter out None values
        filtered_args = [str(arg) for arg in args if arg is not None]
        signature_string = ":".join(filtered_args)
        
        logger.debug(f"Generating signature from: {signature_string}")
        
        return hashlib.md5(signature_string.encode('utf-8')).hexdigest()
    
    def create_payment_link(
        self, 
        payment_id: UUID, 
        amount: float, 
        description: str, 
        user_email: Optional[str] = None
    ) -> str:
        """Create payment link for Robokassa"""
        
        if not self.merchant_login or not self.password1:
            raise ValueError("Robokassa credentials not configured")
        
        out_sum = f"{amount:.2f}"
        inv_id = str(payment_id)
        
        # Generate signature: MerchantLogin:OutSum:InvId:Password1
        signature = self._generate_signature(
            self.merchant_login,
            out_sum,
            inv_id,
            self.password1
        )
        
        # Form parameters
        params = {
            "MerchantLogin": self.merchant_login,
            "OutSum": out_sum,
            "InvId": inv_id,
            "Description": description,
            "SignatureValue": signature,
            "Culture": "ru",
            "Encoding": "utf-8"
        }
        
        # Add email if provided
        if user_email:
            params["Email"] = user_email
        
        # Add test mode flag
        if self.test_mode:
            params["IsTest"] = "1"
        
        # Form URL
        url = f"{self.base_url}?{urlencode(params)}"
        logger.info(f"Created payment link for payment {payment_id}")
        
        return url
    
    def verify_payment_result(self, data: Dict[str, Any]) -> bool:
        """Verify payment result from Robokassa
        
        Result URL signature format: OutSum:InvId:Password2
        """
        try:
            out_sum = data.get("OutSum")
            inv_id = data.get("InvId")
            signature = data.get("SignatureValue", "").upper()
            
            if not all([out_sum, inv_id, signature]):
                logger.error("Missing required parameters for signature verification")
                return False
            
            # Generate expected signature
            expected_signature = self._generate_signature(
                out_sum,
                inv_id,
                self.password2
            ).upper()
            
            is_valid = signature == expected_signature
            
            if not is_valid:
                logger.error(f"Signature mismatch. Expected: {expected_signature}, Got: {signature}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying Robokassa result signature: {e}")
            return False
    
    def verify_success_url(self, data: Dict[str, Any]) -> bool:
        """Verify success URL signature from Robokassa
        
        Success URL signature format: OutSum:InvId:Password1
        """
        try:
            out_sum = data.get("OutSum")
            inv_id = data.get("InvId")
            signature = data.get("SignatureValue", "").upper()
            
            if not all([out_sum, inv_id, signature]):
                logger.error("Missing required parameters for success URL verification")
                return False
            
            # For Success URL, use password1
            expected_signature = self._generate_signature(
                out_sum,
                inv_id,
                self.password1
            ).upper()
            
            is_valid = signature == expected_signature
            
            if not is_valid:
                logger.error(f"Success URL signature mismatch. Expected: {expected_signature}, Got: {signature}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying Robokassa success signature: {e}")
            return False
