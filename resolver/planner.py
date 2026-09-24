import uuid
from typing import Optional

from pqc_migration_tool.schema.models import (
    CryptoIR, MigrationPlan, AssuranceRecord, 
    CryptoRole, CryptoOperation, SecurityStatus, ConfidenceLevel, CodeLocation
)

class MigrationPlanner:
    """
    Phase 3 Engine: Determines the migration plan for a given CryptoIR.
    Enforces ADR-001 (Explicit Abstention).
    """

    def generate_plan(self, ir: CryptoIR) -> AssuranceRecord:
        plan = None
        
        # Enforce ADR-001: Abstain if ambiguous
        if ir.confidence == ConfidenceLevel.AMBIGUOUS:
            plan = MigrationPlan(
                target_algorithm="UNKNOWN",
                target_standard="N/A",
                patch_available=False,
                requires_manual_intervention=True,
                intervention_reason="Role inference failed; cannot safely patch an ambiguous primitive usage.",
                estimated_effort="high"
            )
            return AssuranceRecord(finding=ir, plan=plan)

        # Logic for well-understood primitives
        primitive = ir.primitive_name.lower()

        # RSA Logic
        if "rsa" in primitive:
            if ir.role == CryptoRole.SIGNATURE:
                plan = MigrationPlan(
                    target_algorithm="ML-DSA",
                    target_standard="FIPS 204",
                    patch_available=True,
                    requires_manual_intervention=False,
                    estimated_effort="medium"
                )
            elif ir.role == CryptoRole.KEY_TRANSPORT or ir.role == CryptoRole.ENCRYPTION:
                plan = MigrationPlan(
                    target_algorithm="ML-KEM",
                    target_standard="FIPS 203",
                    patch_available=True,
                    requires_manual_intervention=False,
                    estimated_effort="medium"
                )
        
        # ECC / DH Logic
        elif "x25519" in primitive or "ecdh" in primitive or "dh" in primitive:
            plan = MigrationPlan(
                target_algorithm="X25519 + ML-KEM",
                target_standard="RFC 10024",
                patch_available=True,
                requires_manual_intervention=False,
                estimated_effort="low"
            )
            
        elif "ecdsa" in primitive or "ed25519" in primitive or "dsa" in primitive:
            plan = MigrationPlan(
                target_algorithm="ML-DSA",
                target_standard="FIPS 204",
                patch_available=True,
                requires_manual_intervention=False,
                estimated_effort="low"
            )
            
        # Symmetric / Hashing Logic
        elif "aes" in primitive:
            plan = MigrationPlan(
                target_algorithm="AES-256",
                target_standard="FIPS 197",
                patch_available=False,
                requires_manual_intervention=True,
                intervention_reason="Key rotation required to double key size against Grover's algorithm.",
                estimated_effort="medium"
            )
            
        elif "sha1" in primitive or "md5" in primitive:
             plan = MigrationPlan(
                target_algorithm="SHA-256 / SHA-3",
                target_standard="FIPS 180-4 / FIPS 202",
                patch_available=True,
                requires_manual_intervention=False,
                estimated_effort="low"
            )
             
        elif "sha256" in primitive:
            plan = MigrationPlan(
                target_algorithm="SHA-384 / SHA-512",
                target_standard="FIPS 180-4",
                patch_available=False,
                requires_manual_intervention=True,
                intervention_reason="256-bit hash provides ~128-bit quantum security. Upgrade only if 256-bit PQ security is strictly required.",
                estimated_effort="low"
            )

        # Fallback if unhandled
        if plan is None:
            plan = MigrationPlan(
                target_algorithm="Manual Review",
                target_standard="N/A",
                patch_available=False,
                requires_manual_intervention=True,
                intervention_reason=f"No automated path defined for {primitive} acting as {ir.role.value}",
                estimated_effort="high"
            )

        return AssuranceRecord(finding=ir, plan=plan)
