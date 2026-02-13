import dns.resolver
import re
from fastapi import HTTPException

# Common public providers that are globally trusted
PUBLIC_PROVIDER_ALLOWLIST = {
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "yahoo.com",
    "icloud.com",
    "me.com",
    "proton.me",
    "protonmail.com",
    "aol.com",
}

# Known disposable email providers to block
DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "yopmail.com",
    "tempmail.com",
    "guerrillamail.com",
    "10minutemail.com",
    "temp-mail.org",
}

# Trusted Top-Level Domains (Academic/Institutional/Government)
TRUSTED_TLDS = {
    "edu", "gov", "ac.in", "ac.uk", "org", "edu.in", "mil", "int"
}

# Explicitly allowed custom organization domains (if needed)
KNOWN_ORGANIZATIONS = {
    "microsoft.com", "google.com", "apple.com", "meta.com", "amazon.com"
}

def validate_email_domain(email: str) -> bool:
    """
    STRICT VALIDATION POLICY:
    1. Public Providers (Gmail, etc.) are ALWAYS allowed.
    2. Educational, Governmental, and Trusted TLDs are ALLOWED.
    3. Explicitly whitelisted organizations are ALLOWED.
    4. Everything else is REJECTED to ensure high quality user data.
    """
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="enter a valid domain")

    domain = email.split('@')[-1].lower()

    # 1. Trusted Public Providers
    if domain in PUBLIC_PROVIDER_ALLOWLIST:
        return True

    # 2. Block Known Disposables first
    if domain in DISPOSABLE_DOMAINS:
        raise HTTPException(status_code=400, detail="enter a valid domain")

    # 3. Check Known Organizations Whitelist
    if domain in KNOWN_ORGANIZATIONS:
        return True

    # 4. Check for Trusted TLDs (e.g. .edu, .ac.in)
    # This ensures we allow academic institutions by default.
    if any(domain.endswith(f".{tld}") for tldld in TRUSTED_TLDS for tld in [tldld]):
        # Even for trusted TLDs, we check MX records for existence
        try:
            records = dns.resolver.resolve(domain, 'MX')
            if records:
                return True
        except:
            pass

    # 5. NEW STRICT RULE: Reject any other custom domain (like ex3.com)
    raise HTTPException(status_code=400, detail="enter a valid domain")
