# Backward compatibility shim
from llm.client import ollama_client, OllamaClient


def explain_evidence(evidence: dict) -> str:
    res = ollama_client.analyze_evidence("security_headers", evidence)
    if res:
        return f"{res.why_it_matters}\n\nRemediation:\n{res.remediation}"
    return "AI analysis unavailable. Deterministic evidence collected successfully."