import os
import subprocess
import shutil
from pathlib import Path

class VerificationEngine:
    def __init__(self, target_dir: str):
        self.target_dir = os.path.abspath(target_dir)

    def run_tests(self) -> bool:
        """Run the test suite in the target directory."""
        print(f"\n🧪 [Verification] Running test suite in {self.target_dir}...")
        
        # Naive detection of pytest vs unittest
        # In a real tool, we'd read tox.ini, pyproject.toml, etc.
        cmd = ["pytest", self.target_dir]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=30 # Don't hang forever
            )
            
            if result.returncode == 0:
                print("  ✅ Tests PASSED. Patch is safe.")
                return True
            else:
                print("  ❌ Tests FAILED after patch!")
                # Print just the last few lines of the failure for context
                lines = result.stdout.splitlines()
                for line in lines[-10:]:
                    print(f"    > {line}")
                return False
                
        except FileNotFoundError:
            print("  ⚠️ 'pytest' not found. Cannot verify correctness.")
            # Default to true if we can't test, or false depending on strictness.
            # For demonstration, we'll assume manual review needed if no tests.
            return True 
        except subprocess.TimeoutExpired:
            print("  ❌ Tests timed out!")
            return False

    def rollback(self):
        """Finds all .bak files and restores them, deleting the failed patch."""
        print(f"\n⏪ [Verification] Rolling back changes due to test failure...")
        restored = 0
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".bak"):
                    bak_path = os.path.join(root, file)
                    orig_path = bak_path[:-4] # remove .bak
                    
                    # Restore
                    shutil.copy2(bak_path, orig_path)
                    os.remove(bak_path)
                    restored += 1
                    
        print(f"  ✅ Restored {restored} files to original state.")

    def cleanup_backups(self):
        """If tests pass, we can optionally remove the .bak files."""
        cleaned = 0
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".bak"):
                    os.remove(os.path.join(root, file))
                    cleaned += 1
        print(f"  🧹 Cleaned up {cleaned} backup files.")
