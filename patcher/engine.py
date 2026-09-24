import os
import json
import shutil
from pathlib import Path

class PatcherEngine:
    def __init__(self, report_path: str):
        self.report_path = report_path
        with open(report_path, 'r', encoding='utf-8') as f:
            self.report = json.load(f)

    def run(self):
        records = self.report.get("records", [])
        patched_count = 0
        skipped_count = 0

        print(f"\n🚀 Starting PQMigrate Automated Patcher")
        print(f"=======================================")

        for record in records:
            plan = record.get("plan", {})
            finding = record.get("finding", {})
            
            # Adhere to ADR-001: Abstain if manual intervention is required
            if plan.get("requires_manual_intervention", True):
                skipped_count += 1
                continue
                
            loc = finding.get("location", {})
            file_path = loc.get("file_path")
            line_num = loc.get("line_number")
            primitive = finding.get("primitive_name", "Unknown")
            target_alg = plan.get("target_algorithm", "Unknown")
            target_std = plan.get("target_standard", "N/A")

            if not os.path.exists(file_path):
                print(f"  [ERROR] File not found: {file_path}")
                continue

            # 1. Create a safe backup
            backup_path = f"{file_path}.bak"
            if not os.path.exists(backup_path):
                shutil.copy2(file_path, backup_path)

            # 2. Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if line_num > len(lines):
                print(f"  [ERROR] Line {line_num} out of range in {file_path}")
                continue

            target_line = lines[line_num - 1]
            indentation = target_line[:len(target_line) - len(target_line.lstrip())]

            # 3. Apply semantic transformations
            new_line = target_line
            primitive_lower = primitive.lower()
            
            # Hash migrations
            if "md5" in primitive_lower:
                new_line = new_line.replace('md5', 'sha256')
            elif "sha1" in primitive_lower:
                new_line = new_line.replace('sha1', 'sha256')
            elif "aes" in primitive_lower: # Example: AES-128 to AES-256
                new_line = new_line.replace('128', '256')
            
            if new_line == target_line:
                # No standard simple patch mapped, skip safely
                skipped_count += 1
                continue

            # 4. Inject Compliance Comment
            comment = f"{indentation}# [PQMigrate Auto-Patch] Upgraded {primitive} -> {target_alg} (Ref: {target_std})\n"
            
            lines[line_num - 1] = new_line
            lines.insert(line_num - 1, comment)

            # 5. Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            print(f"  ✅ Patched: {os.path.basename(file_path)}:{line_num} ({primitive} -> {target_alg})")
            patched_count += 1

        print(f"\n=======================================")
        print(f"🏁 Patching Complete.")
        print(f"   Successfully patched : {patched_count}")
        print(f"   Abstained (Manual)   : {skipped_count}")

        # Integration with Phase 4: Verification
        if getattr(self, 'verify', False) and patched_count > 0:
            from pqc_migration_tool.verification.verifier import VerificationEngine
            
            # Assume project root is derived from the first patched file or the report
            # For this MVP, we'll verify the directory of the report's project root if available,
            # but since V2 JSON just has file paths, we'll extract the common dir.
            # Use the directory of the first finding as the test root for simplicity
            test_dir = os.path.dirname(os.path.abspath(records[0].get("finding", {}).get("location", {}).get("file_path", ".")))
            
            verifier = VerificationEngine(test_dir)
            if not verifier.run_tests():
                verifier.rollback()
                print("\n🚨 CRITICAL: Migration failed testing and was safely rolled back.")
            else:
                # Optionally cleanup
                # verifier.cleanup_backups()
                print("\n✅ SUCCESS: Migration passed all tests and is now active.")
        else:
            print(f"   Backups created      : *.bak files next to originals")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python engine.py <report_v2.json> [--verify]")
    else:
        engine = PatcherEngine(sys.argv[1])
        if "--verify" in sys.argv:
            engine.verify = True
        engine.run()
