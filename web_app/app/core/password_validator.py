"""
Password validation utilities for enforcing strong password requirements
"""

import re
from typing import Tuple, List

class PasswordValidator:
    """Password validation with configurable strength requirements"""
    
    def __init__(self, min_length: int = 12, require_uppercase: bool = True, 
                 require_lowercase: bool = True, require_digits: bool = True, 
                 require_special: bool = True):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
    
    def validate(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check minimum length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        # Check for uppercase letters
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letters
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digits
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        # Check for special characters
        if self.require_special and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
        
        # Check for common weak patterns
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password cannot contain 3 or more consecutive identical characters")
        
        if re.search(r'(123|abc|qwe|password|admin|user)', password.lower()):
            errors.append("Password cannot contain common weak patterns")
        
        # Check for keyboard patterns
        keyboard_patterns = [
            'qwerty', 'asdfgh', 'zxcvbn', '123456', '654321',
            'qazwsx', 'edcrfv', 'tgbyhn', 'ujmikl'
        ]
        for pattern in keyboard_patterns:
            if pattern in password.lower():
                errors.append("Password cannot contain keyboard patterns")
                break
        
        return len(errors) == 0, errors
    
    def get_strength_score(self, password: str) -> int:
        """
        Calculate password strength score (0-100)
        
        Returns:
            int: Strength score from 0 (weak) to 100 (strong)
        """
        score = 0
        
        # Base score for length
        score += min(len(password) * 2, 40)
        
        # Character variety bonus
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            score += 15
        
        # Complexity bonus
        unique_chars = len(set(password))
        score += min(unique_chars * 2, 15)
        
        return min(score, 100)

# Default password validator instance
default_validator = PasswordValidator(
    min_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_digits=True,
    require_special=True
)
