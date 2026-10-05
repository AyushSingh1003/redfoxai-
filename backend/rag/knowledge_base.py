from typing import List, Dict, Any


CURATED_KNOWLEDGE_DOCUMENTS = [
    {
        "id": "kb_csp",
        "category": "security_headers",
        "title": "OWASP Content Security Policy (CSP) Guidance",
        "keywords": ["content-security-policy", "csp", "xss", "script-src"],
        "content": (
            "Content-Security-Policy (CSP) is an HTTP header that allows site operators to restrict the "
            "resources (scripts, images, stylesheets) that the browser is allowed to load. A missing or "
            "permissive CSP increases the risk of Cross-Site Scripting (XSS) and data injection attacks. "
            "Remediation: Define a strict default-src 'self' policy and explicitly allow only trusted origins "
            "or cryptographic nonces for dynamic scripts."
        ),
        "reference": "OWASP Secure Headers Project - Content-Security-Policy",
    },
    {
        "id": "kb_hsts",
        "category": "security_headers",
        "title": "OWASP HTTP Strict Transport Security (HSTS)",
        "keywords": ["strict-transport-security", "hsts", "ssl", "tls", "https"],
        "content": (
            "Strict-Transport-Security (HSTS) instructs compliant browsers to communicate with the domain "
            "strictly over HTTPS, preventing SSL-stripping man-in-the-middle (MITM) attacks and protecting "
            "cookie confidentiality in transit. Remediation: Set 'Strict-Transport-Security: max-age=31536000; "
            "includeSubDomains' on production HTTPS endpoints."
        ),
        "reference": "RFC 6797 / OWASP Transport Layer Protection Cheat Sheet",
    },
    {
        "id": "kb_content_type",
        "category": "security_headers",
        "title": "MIME Sniffing Prevention (X-Content-Type-Options)",
        "keywords": ["x-content-type-options", "nosniff", "mime", "sniffing"],
        "content": (
            "The X-Content-Type-Options header set to 'nosniff' prevents browsers from MIME-sniffing a response "
            "away from the declared content-type. Without this, non-executable MIME types (such as image or text) "
            "could be misinterpreted as executable JavaScript. Remediation: Send 'X-Content-Type-Options: nosniff' "
            "on all HTTP responses."
        ),
        "reference": "OWASP Secure Headers Project - X-Content-Type-Options",
    },
    {
        "id": "kb_cookie_httponly",
        "category": "cookie_attributes",
        "title": "OWASP Cookie Security: HttpOnly Attribute",
        "keywords": ["httponly", "cookie", "xss", "session", "stealing"],
        "content": (
            "The HttpOnly flag prevents client-side scripts (such as JavaScript via document.cookie) from "
            "accessing session cookies. This significantly mitigates the impact of Cross-Site Scripting (XSS) "
            "attacks attempting to hijack user sessions. Remediation: Add '; HttpOnly' to all sensitive "
            "Set-Cookie headers."
        ),
        "reference": "OWASP Session Management Cheat Sheet - Cookie Attributes",
    },
    {
        "id": "kb_cookie_secure",
        "category": "cookie_attributes",
        "title": "OWASP Cookie Security: Secure Attribute",
        "keywords": ["secure", "cookie", "tls", "https", "cleartext"],
        "content": (
            "The Secure flag ensures that the cookie is transmitted only over encrypted (HTTPS) connections. "
            "Without this flag, a user visiting an unencrypted HTTP link or on an unencrypted Wi-Fi network could "
            "leak sensitive session cookies over cleartext. Remediation: Append '; Secure' to all Set-Cookie "
            "directives."
        ),
        "reference": "OWASP Session Management Cheat Sheet - Secure Flag",
    },
    {
        "id": "kb_cookie_samesite",
        "category": "cookie_attributes",
        "title": "OWASP Cookie Security: SameSite Attribute",
        "keywords": ["samesite", "csrf", "cookie", "cross-site"],
        "content": (
            "The SameSite attribute (Lax or Strict) controls whether cookies are sent with cross-site requests, "
            "providing robust defense against Cross-Site Request Forgery (CSRF). When omitted or set to None "
            "without proper protection, browsers may automatically attach session cookies to forged external "
            "requests. Remediation: Set '; SameSite=Lax' (or 'Strict') on authentication and state cookies."
        ),
        "reference": "OWASP Cross-Site Request Forgery Prevention Cheat Sheet",
    },
    {
        "id": "kb_http_baseline",
        "category": "http_status",
        "title": "HTTP Service Baseline & Information Disclosure",
        "keywords": ["http_status", "status_code", "latency", "banner"],
        "content": (
            "HTTP response codes and server banners provide initial reconnaissance details. While standard "
            "200 OK responses indicate service availability, excessive verbose banners, debugging headers, "
            "or unhandled error pages (500) can disclose internal framework versions and architecture details. "
            "Remediation: Suppress verbose server headers and ensure centralized error handling."
        ),
        "reference": "OWASP Web Security Testing Guide - Fingerprinting",
    },
]


class KnowledgeRetriever:
    """
    Lightweight, deterministic local RAG knowledge retriever.
    Given evidence and category, retrieves the most relevant OWASP guidelines.
    """

    def __init__(self, documents: List[Dict[str, Any]] = CURATED_KNOWLEDGE_DOCUMENTS):
        self.documents = documents

    def retrieve(self, query_context: str, category: str = "", limit: int = 3) -> List[Dict[str, Any]]:
        context_lower = query_context.lower()
        scored_docs = []

        for doc in self.documents:
            score = 0
            if category and doc["category"] == category:
                score += 3

            for kw in doc["keywords"]:
                if kw in context_lower:
                    score += 2

            if doc["title"].lower() in context_lower:
                score += 2

            if score > 0:
                scored_docs.append((score, doc))

        # Sort descending by score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:limit]]


# Singleton retriever
knowledge_retriever = KnowledgeRetriever()
