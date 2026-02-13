import asyncio
from app.utils.email_validator import validate_email_domain
from fastapi import HTTPException

async def test_email_validator():
    test_cases = [
        ("user@gmail.com", True, "Trusted Public Provider"),
        ("student@mit.edu", True, "Real Intuition Domain"),
        ("user@10minutemail.com", False, "Disposable Domain (Blocked)"),
        ("fake@nonexistentdomainxyz123.com", False, "Non-existent Domain (No MX)"),
        ("invalid-email", False, "Invalid Syntax"),
    ]

    print("🧪 Testing Email Domain Validator...\n")
    
    for email, expected_success, description in test_cases:
        try:
            result = validate_email_domain(email)
            if expected_success:
                print(f"✅ PASS: '{email}' allowed ({description})")
            else:
                print(f"❌ FAIL: '{email}' was allowed but should have been blocked ({description})")
        except HTTPException as e:
            if not expected_success:
                print(f"✅ PASS: '{email}' blocked as expected: {e.detail} ({description})")
            else:
                print(f"❌ FAIL: '{email}' was blocked but should have been allowed: {e.detail} ({description})")
        except Exception as e:
            print(f"💥 ERROR testing '{email}': {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_email_validator())
