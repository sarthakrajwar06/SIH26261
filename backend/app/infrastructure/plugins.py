from typing import Protocol
class VisionPlugin(Protocol):
    def assess(self, evidence: bytes, requirement: dict) -> dict: ...

def assess_presence(requirements: list[str], documents: list[dict]):
    return [{'requirement': r, 'status': 'MANUAL_REVIEW_REQUIRED' if any(d['document_category'] == r for d in documents) else 'MISSING',
             'explanation': 'Evidence presence only; photographs cannot establish full compliance.'} for r in requirements]

def load_model():
    return None  # No validated/licensed model supplied. Never load arbitrary pickle files.
