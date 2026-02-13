import dns.resolver
import re

# Mocking the FastAPI dependency for standalone testing
class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail

# Copying the logic directly for standalone verification
PUBLIC_PROVIDER_ALLOWLIST = {
    "gmail.com", "outlook.com", "hotmail.com", "live.com", "yahoo.com",
    "icloud.com", "me.com", "proton.me", "protonmail.com", "aol.com",
}
DISPOSABLE_DOMAINS = {
    "10minutemail.com", "temp-mail.org", "guerrillamail.com",
    "mailinator.com", "dispostable.com", "dropmail.me", "yopmail.com",
}

def validate_email_domain(email: str) -> bool:
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email syntax")
    domain = email.split('@')[-1].lower()
    if domain in PUBLIC_PROVIDER_ALLOWLIST:
        return True
    if domain in DISPOSABLE_DOMAINS:
        raise HTTPException(status_code=400, detail="Disposable email addresses are not allowed")
    try:
        records = dns.resolver.resolve(domain, 'MX')
        if not records:
            raise HTTPException(status_code=400, detail=f"The domain {domain} does not have valid mail records")
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        raise HTTPException(status_code=400, detail=f"The domain {domain} is unreachable or invalid")
    return True

def run_tests():
    test_cases = [
        ("user@gmail.com", True, "Trusted Public Provider"),
        ("student@mit.edu", True, "Real Intuition Domain"),
        ("user@10minutemail.com", False, "Disposable Domain (Blocked)"),
        ("fake@nonexistentdomainxyz123.com", False, "Non-existent Domain (No MX)"),
        ("invalid-email", False, "Invalid Syntax"),
    ]

    print("🧪 Standalone Testing of Email Domain Validator...\n")
    
    for email, expected_success, description in test_cases:
        try:
            validate_email_domain(email)
            if expected_success:
                print(f"✅ PASS: '{email}' allowed ({description})")
            else:
                print(f"❌ FAIL: '{email}' allowed but should be blocked ({description})")
        except HTTPException as e:
            if not expected_success:
                print(f"✅ PASS: '{email}' blocked as expected: {e.detail} ({description})")
            else:
                print(f"❌ FAIL: '{email}' blocked but should be allowed: {e.detail} ({description})")

if __name__ == "__main__":
    run_tests()
