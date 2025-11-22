"""
Input validators for Indonesian data formats
"""
import re
from datetime import datetime, date
from typing import Optional


def validate_nik(nik: str) -> bool:
    """
    Validate Indonesian NIK (Nomor Induk Kependudukan)
    
    Format: 16 digits
    Structure: PPDDMMYYKKKKSSS
    - PP: Province code (2 digits)
    - DD: District code (2 digits)
    - MM: Month of birth (2 digits, +40 for females)
    - YY: Year of birth (2 digits)
    - KKKK: Sub-district code (4 digits)
    - SSS: Serial number (3 digits)
    - S: Check digit (1 digit)
    
    Args:
        nik: NIK string to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Basic format check
    if not nik or not isinstance(nik, str):
        return False
    
    if not re.match(r'^\d{16}$', nik):
        return False
    
    # Extract components
    province = nik[0:2]
    district = nik[2:4]
    month = int(nik[4:6])
    year = int(nik[6:8])
    
    # Province code validation (11-94)
    if not (11 <= int(province) <= 94):
        return False
    
    # Month validation (01-12 for male, 41-52 for female)
    if month < 1 or (12 < month < 41) or month > 52:
        return False
    
    # Year validation (reasonable range)
    current_year = datetime.now().year % 100
    if year > current_year + 10:  # Not born more than 10 years in future
        return False
    
    return True


def validate_npwp(npwp: str) -> bool:
    """
    Validate Indonesian NPWP (Nomor Pokok Wajib Pajak)
    
    Format: 15 digits (XX.XXX.XXX.X-XXX.XXX) or 20 digits with dashes
    
    Args:
        npwp: NPWP string to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not npwp or not isinstance(npwp, str):
        return False
    
    # Remove dots and dashes
    npwp_clean = npwp.replace('.', '').replace('-', '').replace(' ', '')
    
    # Should be 15 digits
    if not re.match(r'^\d{15}$', npwp_clean):
        return False
    
    return True


def validate_phone_number(phone: str) -> bool:
    """
    Validate Indonesian phone number
    
    Formats accepted:
    - 08XXXXXXXXX (local format)
    - +628XXXXXXXXX (international format)
    - 628XXXXXXXXX (international without +)
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove spaces, dashes, parentheses
    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check formats
    patterns = [
        r'^08\d{8,11}$',        # Local: 08XX-XXXX-XXXX
        r'^\+628\d{8,11}$',     # International: +628XX-XXXX-XXXX
        r'^628\d{8,11}$',       # International without +
    ]
    
    return any(re.match(pattern, phone_clean) for pattern in patterns)


def validate_email(email: str) -> bool:
    """
    Validate email address
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_postal_code(postal_code: str) -> bool:
    """
    Validate Indonesian postal code
    
    Format: 5 digits
    
    Args:
        postal_code: Postal code to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not postal_code or not isinstance(postal_code, str):
        return False
    
    return bool(re.match(r'^\d{5}$', postal_code))


def calculate_age(date_of_birth: date) -> int:
    """
    Calculate age from date of birth
    
    Args:
        date_of_birth: Date of birth
    
    Returns:
        Age in years
    """
    today = date.today()
    age = today.year - date_of_birth.year
    
    # Adjust if birthday hasn't occurred this year
    if today.month < date_of_birth.month or \
       (today.month == date_of_birth.month and today.day < date_of_birth.day):
        age -= 1
    
    return age


def validate_age_range(date_of_birth: date, min_age: int = 21, max_age: int = 65) -> bool:
    """
    Validate age is within acceptable range
    
    Args:
        date_of_birth: Date of birth
        min_age: Minimum age (default 21)
        max_age: Maximum age (default 65)
    
    Returns:
        True if age is within range, False otherwise
    """
    age = calculate_age(date_of_birth)
    return min_age <= age <= max_age


def normalize_nik(nik: str) -> str:
    """
    Normalize NIK by removing spaces and special characters
    
    Args:
        nik: NIK to normalize
    
    Returns:
        Normalized NIK (16 digits)
    """
    return re.sub(r'[^\d]', '', nik)


def normalize_npwp(npwp: str) -> str:
    """
    Normalize NPWP by removing dots and dashes
    
    Args:
        npwp: NPWP to normalize
    
    Returns:
        Normalized NPWP (15 digits)
    """
    return re.sub(r'[^\d]', '', npwp)


# Example usage:
# if validate_nik("3273010101990001"):
#     print("Valid NIK")
# 
# age = calculate_age(date(1990, 1, 1))
# print(f"Age: {age} years")
