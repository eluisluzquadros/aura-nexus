#!/usr/bin/env python3
"""
Test script for contact validation fixes
Tests the critical phone number and email validation improvements
"""

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.lead_processor import LeadProcessor
from src.core.api_manager import APIManager
from src.infrastructure.cache_system import SmartMultiLevelCache

def test_phone_validation():
    """Test phone number validation with known problematic cases"""
    print("Testing Phone Number Validation")
    print("=" * 50)
    
    # Create a minimal LeadProcessor for testing
    processor = LeadProcessor({})
    
    # Test cases: [phone_number, expected_result, description]
    test_cases = [
        # CRITICAL FIXES - These should all return False now
        ("25798914189", False, "Specific fake number from customer data"),
        ("1659080345", False, "Another specific fake number (timestamp)"),
        ("10000000", False, "Obvious fake pattern"),
        ("000000000", False, "All zeros"),
        ("111111111", False, "All ones"),
        ("123456789", False, "Sequential numbers"),
        ("999999999", False, "All nines"),
        
        # Timestamp detection - these should all return False
        ("1643723400", False, "Unix timestamp (10 digits)"),
        ("1659080345000", False, "Unix timestamp (13 digits)"),
        ("1577836800", False, "New Year 2020 timestamp"),
        
        # Valid Brazilian phones - these should return True
        ("11987654321", True, "Valid São Paulo mobile"),
        ("21987654321", True, "Valid Rio mobile"),
        ("1133456789", True, "Valid São Paulo landline"),
        ("2133456789", True, "Valid Rio landline"),
        ("+5511987654321", True, "Valid mobile with country code"),
        
        # Invalid but not fake patterns
        ("123", False, "Too short"),
        ("12345678901234", False, "Too long"),
        ("abc123def456", False, "Contains letters"),
        
        # Edge cases
        ("", False, "Empty string"),
        (None, False, "None value"),
    ]
    
    passed = 0
    failed = 0
    
    for phone, expected, description in test_cases:
        try:
            result = processor._is_valid_brazilian_phone(phone) if phone else False
            status = "PASS" if result == expected else "FAIL"
            
            if result == expected:
                passed += 1
            else:
                failed += 1
                print(f"{status} {phone:<15} -> {result:<5} (expected {expected}) - {description}")
            
            # Always show critical fixes results
            if phone in ["25798914189", "1659080345", "10000000"]:
                print(f"{status} {phone:<15} -> {result:<5} (expected {expected}) - {description}")
                
        except Exception as e:
            print(f"ERROR {phone:<15} -> Exception: {e} - {description}")
            failed += 1
    
    print(f"\nPhone Validation Results: {passed} passed, {failed} failed")
    return failed == 0

def test_email_validation():
    """Test email validation improvements"""
    print("\nTesting Email Validation")
    print("=" * 50)
    
    # Create a minimal LeadProcessor for testing
    processor = LeadProcessor({})
    
    # Test cases: [email, expected_result, description]
    test_cases = [
        # Valid emails
        ("user@example.com.br", True, "Valid Brazilian domain"),
        ("contact@company.com", True, "Valid company email"),
        ("info@business.org", True, "Valid org domain"),
        
        # Invalid/fake emails - should return False
        ("test@example.com", False, "Test domain"),
        ("fake@fake.com", False, "Fake domain"),
        ("dummy@dummy.com", False, "Dummy domain"),
        ("admin@test.com", False, "Test domain"),
        ("noreply@example.org", False, "Example domain"),
        
        # Malformed emails
        ("invalid-email", False, "No @ symbol"),
        ("@domain.com", False, "Missing local part"),
        ("user@", False, "Missing domain"),
        ("user..name@domain.com", False, "Double dots"),
        (".user@domain.com", False, "Starts with dot"),
        ("user.@domain.com", False, "Ends with dot"),
        
        # Edge cases
        ("", False, "Empty string"),
        (None, False, "None value"),
    ]
    
    passed = 0
    failed = 0
    
    for email, expected, description in test_cases:
        try:
            result = processor._is_valid_email_enhanced(email) if email else False
            status = "PASS" if result == expected else "FAIL"
            
            if result == expected:
                passed += 1
            else:
                failed += 1
            
            # Show all results for email testing
            print(f"{status} {email:<25} -> {result:<5} (expected {expected}) - {description}")
                
        except Exception as e:
            print(f"ERROR {email:<25} -> Exception: {e} - {description}")
            failed += 1
    
    print(f"\nEmail Validation Results: {passed} passed, {failed} failed")
    return failed == 0

def test_timestamp_detection():
    """Test specific timestamp detection logic"""
    print("\nTesting Timestamp Detection")
    print("=" * 50)
    
    # Create a minimal LeadProcessor for testing
    processor = LeadProcessor({})
    
    # Known timestamps that were appearing as phone numbers
    timestamps = [
        "25798914189",  # From customer data
        "1659080345",   # From customer data  
        "1643723400",   # Jan 2022
        "1577836800",   # Jan 2020
        "1893456000",   # Jan 2030
        "1659080345000", # Millisecond timestamp
    ]
    
    all_detected = True
    
    for timestamp in timestamps:
        is_fake = processor._is_timestamp_or_fake(timestamp)
        status = "DETECTED" if is_fake else "MISSED"
        print(f"{status} {timestamp} - {'Correctly identified as fake' if is_fake else 'Should be detected as fake!'}")
        
        if not is_fake:
            all_detected = False
    
    print(f"\nTimestamp Detection: {'All timestamps detected' if all_detected else 'Some timestamps missed!'}")
    return all_detected

def test_integration():
    """Test the full contact extraction and validation pipeline"""
    print("\nTesting Full Integration")
    print("=" * 50)
    
    # Create a minimal LeadProcessor for testing
    processor = LeadProcessor({})
    
    # Sample text with mixed good and bad contacts
    test_text = """
    Contact us at:
    Email: valid@company.com.br
    Phone: (11) 98765-4321
    Also: fake@example.com
    Bad phone: 25798914189
    Another phone: 1659080345
    Valid landline: (11) 3456-7890
    """
    
    # Test phone extraction
    phone = processor._extract_phone_from_text(test_text)
    print(f"Extracted phone: '{phone}'")
    
    # Test email extraction  
    emails = processor._extract_emails(test_text)
    print(f"Extracted emails: {emails}")
    
    # Validate results
    valid_phone = phone and processor._is_valid_brazilian_phone(phone)
    valid_emails = all(processor._is_valid_email_enhanced(email) for email in emails)
    
    print(f"✅ Phone valid: {valid_phone}")
    print(f"✅ All emails valid: {valid_emails}")
    
    # Check that fake numbers were rejected
    fake_rejected = not any(fake in phone for fake in ["25798914189", "1659080345"] if phone)
    print(f"✅ Fake phones rejected: {fake_rejected}")
    
    return valid_phone and valid_emails and fake_rejected

def main():
    """Run all validation tests"""
    print("CRITICAL CONTACT DATA QUALITY VALIDATION TESTS")
    print("=" * 60)
    print("Testing fixes for 78% fake contact issue")
    print("Expected outcome: Zero fake contacts in output\n")
    
    # Run all tests
    phone_test = test_phone_validation()
    email_test = test_email_validation()
    timestamp_test = test_timestamp_detection()
    integration_test = test_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    tests_passed = sum([phone_test, email_test, timestamp_test, integration_test])
    total_tests = 4
    
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {tests_passed/total_tests*100:.1f}%")
    
    if tests_passed == total_tests:
        print("ALL TESTS PASSED! Contact quality fixes are working correctly.")
        print("Expected impact: Transform from 22% to 95%+ contact validity rate")
        print("Ready for deployment to fix the customer crisis!")
    else:
        print("Some tests failed. Review fixes before deployment.")
    
    print("\n" + "=" * 60)
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)