import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any

class ProtocolContext(str, Enum):
    JWT = "jwt"
    POSSIBLE_JWT = "possible_jwt"
    SSH = "ssh"
    POSSIBLE_SSH = "possible_ssh"
    TLS = "tls"
    UNKNOWN = "unknown"

class CryptoRole(str, Enum):
    SIGNATURE = "signature"
    KEY_ESTABLISHMENT = "key_establishment"
    KEY_TRANSPORT = "key_transport"
    ENCRYPTION = "encryption"
    AUTHENTICATION = "authentication"
    HASH = "hash"
    MAC = "mac"
    CERTIFICATE_IDENTITY = "certificate_identity"
    UNKNOWN = "unknown"

class CryptoOperation(str, Enum):
    SIGN = "sign"
    VERIFY = "verify"
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"
    GENERATE = "generate"
    EXCHANGE = "exchange"
    ENCAPSULATE = "encapsulate"
    DECAPSULATE = "decapsulate"
    CONFIGURE = "configure"
    UNKNOWN = "unknown"
    HASH = "hash"
    DERIVE = "derive"

class SecurityStatus(str, Enum):
    QUANTUM_VULNERABLE = "quantum_vulnerable"
    QUANTUM_SECURITY_REDUCED = "quantum_security_reduced"
    STANDARDIZED_PQC = "standardized_pqc"
    CONTEXT_DEPENDENT = "context_dependent"
    DEPRECATED_CLASSICALLY = "deprecated_classically"
    UNKNOWN = "unknown"

class ConfidenceLevel(str, Enum):
    DIRECT = "direct"
    INFERRED = "inferred"
    AMBIGUOUS = "ambiguous"

@dataclass
class CodeLocation:
    file_path: str
    line_number: int
    column: Optional[int] = None
    context_snippet: Optional[str] = None

@dataclass
class CryptoIR:
    """Internal Representation of a Cryptographic usage site."""
    id: str
    primitive_name: str
    location: CodeLocation
    role: CryptoRole
    operation: CryptoOperation
    status: SecurityStatus
    confidence: ConfidenceLevel
    detection_type: str
    
    # D6: Context Tracking
    protocol_context: ProtocolContext = ProtocolContext.UNKNOWN
    context_evidence: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['role'] = self.role.value
        d['operation'] = self.operation.value
        d['status'] = self.status.value
        d['confidence'] = self.confidence.value
        d['protocol_context'] = self.protocol_context.value
        return d

@dataclass
class MigrationPlan:
    """A proposed change to migrate a CryptoIR to PQC."""
    target_algorithm: str
    target_standard: str
    patch_available: bool
    requires_manual_intervention: bool
    intervention_reason: Optional[str] = None
    estimated_effort: str = "unknown"
    
    # D7: Originating Rule ID
    rule_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AssuranceRecord:
    finding: CryptoIR
    plan: Optional[MigrationPlan] = None
    tests_passed: bool = False
    verified_by_human: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'finding': self.finding.to_dict(),
            'plan': self.plan.to_dict() if self.plan else None,
            'tests_passed': self.tests_passed,
            'verified_by_human': self.verified_by_human
        }

@dataclass
class ProjectReport:
    project_name: str
    scan_timestamp: str
    files_scanned: int
    total_findings: int
    records: List[AssuranceRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_name': self.project_name,
            'scan_timestamp': self.scan_timestamp,
            'files_scanned': self.files_scanned,
            'total_findings': self.total_findings,
            'records': [r.to_dict() for r in self.records]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
