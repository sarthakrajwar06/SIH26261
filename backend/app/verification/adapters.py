from typing import Protocol
from datetime import datetime, timezone

class VerificationAdapter(Protocol):
    def verify(self, document: dict, fields: list[dict]) -> dict: ...

class UnconfiguredAdapter:
    def __init__(self, mode='OFFICIAL'): self.mode = mode
    def verify(self, document, fields):
        return dict(verification_mode=self.mode, status='UNSUPPORTED', source_identifier='unconfigured',
                    matched_fields=[], mismatched_fields=[], response_reference=None,
                    verified_at=datetime.now(timezone.utc).isoformat(),
                    explanation='No authorized adapter or trust configuration. Follow up manually.')

class QRAdapter(UnconfiguredAdapter):
    def __init__(self): super().__init__('QR')

class DigitalSignatureAdapter(UnconfiguredAdapter):
    def __init__(self): super().__init__('DIGITAL_SIGNATURE')

class MockAdapter:
    def __init__(self, scenario='pending'): self.scenario = scenario
    def verify(self, document, fields):
        result = UnconfiguredAdapter('SIMULATED').verify(document, fields)
        result.update(status={'success':'VERIFIED','mismatch':'MISMATCH_DETECTED','unavailable':'SOURCE_UNAVAILABLE','pending':'PENDING'}[self.scenario],
                      source_identifier='LOCAL_SYNTHETIC_ADAPTER', explanation='SIMULATED response; no issuing authority was contacted.')
        if self.scenario == 'success': result['matched_fields'] = [f['field_name'] for f in fields]
        if self.scenario == 'mismatch': result['mismatched_fields'] = ['institution_identifier']
        return result
