import json
import unittest
from datetime import datetime

from pqc_migration_tool.schema.models import (
    CryptoIR, CodeLocation, CryptoRole, CryptoOperation, 
    SecurityStatus, ConfidenceLevel, MigrationPlan, AssuranceRecord, ProjectReport
)

class TestSchemaValidation(unittest.TestCase):

    def test_schema_generation(self):
        # 1. Create a Code Location
        loc = CodeLocation(
            file_path="src/main.py",
            line_number=45,
            context_snippet="signature = rsa_key.sign(data)"
        )

        # 2. Create the CryptoIR
        finding = CryptoIR(
            id="test-hash-001",
            primitive_name="cryptography.hazmat.primitives.asymmetric.rsa",
            location=loc,
            role=CryptoRole.SIGNATURE,
            operation=CryptoOperation.SIGN,
            status=SecurityStatus.QUANTUM_VULNERABLE,
            confidence=ConfidenceLevel.DIRECT,
            detection_type="operation_candidate"
        )

        # 3. Create the Migration Plan
        plan = MigrationPlan(
            target_algorithm="ML-DSA-44",
            target_standard="FIPS 204",
            patch_available=False,
            requires_manual_intervention=False,
            estimated_effort="low"
        )

        # 4. Create Assurance Record
        record = AssuranceRecord(
            finding=finding,
            plan=plan,
            tests_passed=False,
            verified_by_human=False
        )

        # 5. Create Root Report
        report = ProjectReport(
            project_name="test-project",
            scan_timestamp=datetime.utcnow().isoformat(),
            files_scanned=1,
            total_findings=1,
            records=[record]
        )

        # 6. Validate JSON Serialization
        out_dict = report.to_dict()
        out_json = report.to_json()

        self.assertEqual(out_dict['project_name'], "test-project")
        self.assertEqual(out_dict['records'][0]['finding']['role'], "signature")
        self.assertEqual(out_dict['records'][0]['plan']['target_standard'], "FIPS 204")
        
        # Verify JSON is serializable (no Enum serialization crash)
        parsed = json.loads(out_json)
        self.assertEqual(parsed['records'][0]['finding']['operation'], "sign")

if __name__ == '__main__':
    unittest.main()
