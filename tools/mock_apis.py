"""
Mock API implementations for credit underwriting agents.
These simulate real-world external API calls with realistic responses and random variations.
"""

import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json


# Mock database of known entities for realistic responses
MOCK_IDENTITY_DATABASE = {
    "valid": {
        "111-22-3333": {
            "name": "John Doe",
            "address": "123 Main St, New York, NY 10001",
            "identity_verified": True,
            "identity_theft_flags": False,
            "address_history_months": 36,
            "government_verified": True
        },
        "222-33-4444": {
            "name": "Jane Smith",
            "address": "456 Oak Ave, Los Angeles, CA 90001",
            "identity_verified": True,
            "identity_theft_flags": False,
            "address_history_months": 24,
            "government_verified": True
        },
    },
    "suspicious": {
        "333-44-5555": {
            "name": "Bob Johnson",
            "address": "789 Elm St, Chicago, IL 60601",
            "identity_verified": False,
            "identity_theft_flags": True,
            "address_history_months": 3,
            "government_verified": False
        },
    }
}

MOCK_INCOME_DATABASE = {
    "111-22-3333": {
        "employer": "Tech Corp Inc",
        "employment_status": "full_time",
        "annual_income": 85000,
        "employment_months": 48,
        "income_verified": True,
        "documentation_complete": True
    },
    "222-33-4444": {
        "employer": "Healthcare Solutions LLC",
        "employment_status": "full_time",
        "annual_income": 120000,
        "employment_months": 60,
        "income_verified": True,
        "documentation_complete": True
    },
    "333-44-5555": {
        "employer": "Unknown",
        "employment_status": "self_employed",
        "annual_income": 45000,
        "employment_months": 2,
        "income_verified": False,
        "documentation_complete": False
    },
}

MOCK_OFAC_LIST = [
    "444-55-6666",
    "555-66-7777",
]

MOCK_FRAUD_PATTERNS = {
    "high_risk_ips": ["192.168.1.100", "10.0.0.50"],
    "high_velocity_ssns": ["333-44-5555", "666-77-8888"],
}


def check_identity(ssn: str, name: str, address: str) -> Dict:
    """
    Mock identity verification API.
    
    Checks:
    - SSN validation against credit bureau
    - Identity theft flags
    - Address history
    - Government database cross-reference
    
    Args:
        ssn: Social Security Number
        name: Applicant name
        address: Current address
        
    Returns:
        Dict with verification results
    """
    # Introduce some randomness for realistic simulation
    response_delay = random.uniform(0.5, 2.0)  # Simulate API latency
    
    # Check if SSN is in our mock database
    all_records = {**MOCK_IDENTITY_DATABASE["valid"], **MOCK_IDENTITY_DATABASE["suspicious"]}
    
    if ssn in all_records:
        record = all_records[ssn]
        
        # Add slight randomness to confidence scores
        base_confidence = 0.95 if record["identity_verified"] else 0.40
        confidence_variation = random.uniform(-0.05, 0.05)
        confidence = max(0.0, min(1.0, base_confidence + confidence_variation))
        
        return {
            "success": True,
            "ssn": ssn,
            "ssn_valid": record["identity_verified"],
            "name_match": record["name"].lower() == name.lower(),
            "address_match": record["address"].lower() in address.lower(),
            "identity_theft_flags": record["identity_theft_flags"],
            "address_history_months": record["address_history_months"],
            "government_verified": record["government_verified"],
            "confidence_score": round(confidence, 2),
            "checks_passed": {
                "ssn_validation": record["identity_verified"],
                "identity_theft_check": not record["identity_theft_flags"],
                "address_verification": record["address_history_months"] >= 6,
                "government_database_check": record["government_verified"]
            },
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": int(response_delay * 1000)
        }
    else:
        # Unknown SSN - simulate not found scenario
        return {
            "success": False,
            "ssn": ssn,
            "ssn_valid": False,
            "name_match": False,
            "address_match": False,
            "identity_theft_flags": False,
            "address_history_months": 0,
            "government_verified": False,
            "confidence_score": 0.0,
            "checks_passed": {
                "ssn_validation": False,
                "identity_theft_check": True,
                "address_verification": False,
                "government_database_check": False
            },
            "error": "SSN not found in credit bureau records",
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": int(response_delay * 1000)
        }


def verify_income(
    ssn: str,
    stated_income: float,
    employer: Optional[str] = None,
    total_debt_payments: Optional[float] = None
) -> Dict:
    """
    Mock income verification API.
    
    Checks:
    - Employment status
    - Income documentation
    - Income stability (employment duration)
    - DTI ratio calculation
    
    Args:
        ssn: Social Security Number
        stated_income: Income claimed by applicant
        employer: Employer name (optional)
        total_debt_payments: Monthly debt obligations for DTI calc
        
    Returns:
        Dict with income verification results
    """
    response_delay = random.uniform(0.3, 1.5)
    
    if ssn in MOCK_INCOME_DATABASE:
        record = MOCK_INCOME_DATABASE[ssn]
        
        # Calculate income variance
        actual_income = record["annual_income"]
        income_variance = abs(stated_income - actual_income) / actual_income if actual_income > 0 else 1.0
        income_match = income_variance < 0.15  # Within 15%
        
        # Calculate DTI if debt payments provided
        monthly_income = actual_income / 12
        dti_ratio = None
        if total_debt_payments and monthly_income > 0:
            dti_ratio = round(total_debt_payments / monthly_income, 3)
        
        # Employment stability check (need 3+ months)
        employment_stable = record["employment_months"] >= 3
        
        # Confidence calculation
        base_confidence = 0.85 if record["income_verified"] else 0.50
        confidence_variation = random.uniform(-0.05, 0.05)
        confidence = max(0.0, min(1.0, base_confidence + confidence_variation))
        
        return {
            "success": True,
            "ssn": ssn,
            "employer": record["employer"],
            "employment_status": record["employment_status"],
            "stated_income": stated_income,
            "verified_income": actual_income,
            "income_match": income_match,
            "income_variance_pct": round(income_variance * 100, 2),
            "employment_months": record["employment_months"],
            "employment_stable": employment_stable,
            "documentation_complete": record["documentation_complete"],
            "dti_ratio": dti_ratio,
            "dti_within_limit": dti_ratio < 0.43 if dti_ratio else None,
            "confidence_score": round(confidence, 2),
            "checks_passed": {
                "employment_verification": record["employment_status"] in ["full_time", "part_time"],
                "income_documentation": record["documentation_complete"],
                "income_stability": employment_stable,
                "dti_calculation": dti_ratio < 0.43 if dti_ratio else True
            },
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": int(response_delay * 1000)
        }
    else:
        return {
            "success": False,
            "ssn": ssn,
            "stated_income": stated_income,
            "verified_income": None,
            "income_match": False,
            "employment_stable": False,
            "documentation_complete": False,
            "dti_ratio": None,
            "confidence_score": 0.0,
            "checks_passed": {
                "employment_verification": False,
                "income_documentation": False,
                "income_stability": False,
                "dti_calculation": False
            },
            "error": "Unable to verify income - SSN not found",
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": int(response_delay * 1000)
        }


def check_ofac(ssn: str, name: str) -> Dict:
    """
    Mock OFAC (Office of Foreign Assets Control) sanctions list check.
    
    This is a CRITICAL check with zero tolerance - any match requires denial.
    
    Args:
        ssn: Social Security Number
        name: Applicant name
        
    Returns:
        Dict with OFAC screening results
    """
    response_delay = random.uniform(0.2, 0.8)
    
    # Check against mock OFAC list
    on_ofac_list = ssn in MOCK_OFAC_LIST
    
    # Simulate name fuzzy matching
    name_similarity = random.uniform(0.0, 0.3) if on_ofac_list else random.uniform(0.0, 0.1)
    
    return {
        "success": True,
        "ssn": ssn,
        "name": name,
        "on_ofac_list": on_ofac_list,
        "match_type": "exact" if on_ofac_list else "none",
        "name_similarity_score": round(name_similarity, 3),
        "sanctions_found": on_ofac_list,
        "screening_passed": not on_ofac_list,
        "lists_checked": ["SDN", "Non-SDN", "Sectoral Sanctions"],
        "confidence_score": 1.0 if not on_ofac_list else 0.0,
        "timestamp": datetime.now().isoformat(),
        "response_time_ms": int(response_delay * 1000)
    }


def check_fraud_indicators(
    ssn: str,
    device_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    application_count_30d: int = 1
) -> Dict:
    """
    Mock fraud indicator analysis.
    
    Checks:
    - Credit inquiry patterns
    - Application velocity (multiple apps in short time)
    - Device/IP fingerprinting
    - Known fraud patterns
    
    Args:
        ssn: Social Security Number
        device_id: Device fingerprint
        ip_address: IP address of application
        application_count_30d: Number of applications in last 30 days
        
    Returns:
        Dict with fraud analysis results
    """
    response_delay = random.uniform(0.5, 1.5)
    
    # Check velocity (high-risk if SSN in velocity list or too many apps)
    high_velocity = ssn in MOCK_FRAUD_PATTERNS["high_velocity_ssns"] or application_count_30d > 3
    
    # Check IP risk
    high_risk_ip = ip_address in MOCK_FRAUD_PATTERNS["high_risk_ips"] if ip_address else False
    
    # Simulate credit inquiry data
    recent_inquiries = random.randint(0, 8) if high_velocity else random.randint(0, 2)
    inquiry_pattern_suspicious = recent_inquiries > 5
    
    # Generate synthetic credit bureau inquiry data
    inquiry_dates = []
    for i in range(recent_inquiries):
        days_ago = random.randint(1, 30)
        inquiry_dates.append((datetime.now() - timedelta(days=days_ago)).isoformat()[:10])
    
    # Calculate fraud risk score
    fraud_indicators = []
    fraud_score = 0.0
    
    if high_velocity:
        fraud_indicators.append("high_application_velocity")
        fraud_score += 0.3
    
    if inquiry_pattern_suspicious:
        fraud_indicators.append("suspicious_inquiry_pattern")
        fraud_score += 0.25
    
    if high_risk_ip:
        fraud_indicators.append("high_risk_ip_address")
        fraud_score += 0.25
    
    if recent_inquiries > 8:
        fraud_indicators.append("excessive_credit_inquiries")
        fraud_score += 0.2
    
    fraud_score = min(1.0, fraud_score)
    confidence = 1.0 - fraud_score
    
    return {
        "success": True,
        "ssn": ssn,
        "fraud_indicators": fraud_indicators,
        "fraud_risk_score": round(fraud_score, 2),
        "confidence_score": round(confidence, 2),
        "details": {
            "credit_inquiries": {
                "count_30d": recent_inquiries,
                "inquiry_dates": inquiry_dates[:5],  # Show last 5
                "pattern_suspicious": inquiry_pattern_suspicious
            },
            "application_velocity": {
                "applications_30d": application_count_30d,
                "velocity_flag": high_velocity
            },
            "device_fingerprint": {
                "device_id": device_id,
                "ip_address": ip_address,
                "ip_risk_level": "high" if high_risk_ip else "low",
                "device_match": random.choice([True, False]) if device_id else None
            }
        },
        "checks_passed": {
            "inquiry_pattern_check": not inquiry_pattern_suspicious,
            "velocity_check": not high_velocity,
            "device_ip_check": not high_risk_ip
        },
        "screening_passed": len(fraud_indicators) == 0,
        "timestamp": datetime.now().isoformat(),
        "response_time_ms": int(response_delay * 1000)
    }


def get_credit_bureau_data(ssn: str) -> Dict:
    """
    Mock credit bureau data retrieval.
    
    Returns comprehensive credit report data including:
    - Credit score
    - Account history
    - Payment history
    - Public records
    - Inquiries
    
    Args:
        ssn: Social Security Number
        
    Returns:
        Dict with credit bureau report
    """
    response_delay = random.uniform(1.0, 2.5)
    
    # Generate synthetic credit data
    all_records = {**MOCK_IDENTITY_DATABASE["valid"], **MOCK_IDENTITY_DATABASE["suspicious"]}
    
    if ssn in all_records:
        # Generate realistic credit score based on identity status
        is_good_credit = ssn in MOCK_IDENTITY_DATABASE["valid"]
        
        if is_good_credit:
            credit_score = random.randint(680, 820)
            payment_history_pct = random.uniform(0.92, 1.0)
            delinquencies = random.randint(0, 1)
        else:
            credit_score = random.randint(520, 650)
            payment_history_pct = random.uniform(0.65, 0.85)
            delinquencies = random.randint(2, 5)
        
        # Generate account mix
        num_accounts = random.randint(3, 12)
        total_credit_limit = random.randint(15000, 75000)
        total_balance = random.randint(2000, int(total_credit_limit * 0.6))
        utilization = round(total_balance / total_credit_limit, 3) if total_credit_limit > 0 else 0
        
        return {
            "success": True,
            "ssn": ssn,
            "credit_score": credit_score,
            "score_range": "300-850",
            "score_factors": [
                "Payment History (35%)",
                "Credit Utilization (30%)",
                "Length of Credit History (15%)",
                "Credit Mix (10%)",
                "New Credit (10%)"
            ],
            "summary": {
                "total_accounts": num_accounts,
                "open_accounts": num_accounts - random.randint(0, 2),
                "total_credit_limit": total_credit_limit,
                "total_balance": total_balance,
                "utilization_ratio": utilization,
                "delinquencies": delinquencies,
                "public_records": 0 if is_good_credit else random.randint(0, 2),
                "inquiries_6m": random.randint(0, 3),
                "inquiries_12m": random.randint(1, 5),
                "oldest_account_months": random.randint(24, 180),
                "payment_history_pct": round(payment_history_pct, 3)
            },
            "tradelines": [
                {
                    "type": "revolving",
                    "creditor": "Major Bank Credit Card",
                    "balance": random.randint(500, 5000),
                    "limit": random.randint(5000, 15000),
                    "payment_status": "current"
                },
                {
                    "type": "installment",
                    "creditor": "Auto Loan",
                    "balance": random.randint(10000, 25000),
                    "limit": random.randint(20000, 35000),
                    "payment_status": "current"
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": int(response_delay * 1000)
        }
    else:
        return {
            "success": False,
            "ssn": ssn,
            "error": "No credit file found",
            "thin_file": True,
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": int(response_delay * 1000)
        }


# Helper function to get test SSNs for demos
def get_test_ssns() -> Dict[str, List[str]]:
    """
    Returns lists of test SSNs for different scenarios.
    
    Returns:
        Dict with categorized test SSNs
    """
    return {
        "valid_low_risk": ["111-22-3333", "222-33-4444"],
        "suspicious_high_risk": ["333-44-5555"],
        "ofac_match": ["444-55-6666", "555-66-7777"],
        "not_found": ["999-99-9999"],
    }


if __name__ == "__main__":
    # Quick test of all mock APIs
    print("=" * 70)
    print("MOCK API TESTING")
    print("=" * 70)
    
    test_ssn = "111-22-3333"
    
    print("\n1. Identity Check:")
    print("-" * 70)
    result = check_identity(test_ssn, "John Doe", "123 Main St, New York, NY")
    print(json.dumps(result, indent=2))
    
    print("\n2. Income Verification:")
    print("-" * 70)
    result = verify_income(test_ssn, 85000, "Tech Corp Inc", 2500)
    print(json.dumps(result, indent=2))
    
    print("\n3. OFAC Check:")
    print("-" * 70)
    result = check_ofac(test_ssn, "John Doe")
    print(json.dumps(result, indent=2))
    
    print("\n4. Fraud Indicators:")
    print("-" * 70)
    result = check_fraud_indicators(test_ssn, "device-123", "192.168.1.1", 2)
    print(json.dumps(result, indent=2))
    
    print("\n5. Credit Bureau Data:")
    print("-" * 70)
    result = get_credit_bureau_data(test_ssn)
    print(json.dumps(result, indent=2))
