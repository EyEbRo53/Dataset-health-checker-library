import os
import shutil
from pathlib import Path

class Cleaner:
    def __init__(self, dataset_path: str, report_data: dict):
        self.dataset_path = Path(dataset_path).resolve()
        self.report_data = report_data
        self.quarantine_dir = self.dataset_path / "_quarantine"

    def clean(self):
        """
        Moves corrupt and duplicate files to a _quarantine folder.
        """
        if not self.quarantine_dir.exists():
            self.quarantine_dir.mkdir(parents=True)

        print(f"Cleaning dataset... Quarantine folder: {self.quarantine_dir}")
        
        self._move_corrupt_files()
        self._move_duplicate_files()
        self._move_suspicious_files()

    def _safe_move(self, src_path: Path, reason: str):
        """
        Moves a file to quarantine, preserving relative path structure.
        """
        try:
            # Calculate relative path from dataset root
            try:
                rel_path = src_path.relative_to(self.dataset_path)
            except ValueError:
                # If file is not inside dataset path (should not happen?), just use filename
                rel_path = Path(src_path.name)

            # Destination
            dest_path = self.quarantine_dir / reason / rel_path
            
            # Ensure dest dir exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move
            if src_path.exists():
                shutil.move(str(src_path), str(dest_path))
                print(f"moved: {src_path.name} -> {dest_path}")
            else:
                print(f"skipped (not found): {src_path}")
                
        except Exception as e:
            print(f"Error moving {src_path}: {e}")

    def _move_corrupt_files(self):
        corrupt_files = self.report_data["sections"].get("corrupt_files", [])
        if not corrupt_files:
            return

        print(f"Moving {len(corrupt_files)} corrupt files...")
        for entry in corrupt_files:
            file_path = Path(entry["file_path"]).resolve()
            self._safe_move(file_path, "corrupt")

    def _move_duplicate_files(self):
        duplicates = self.report_data["sections"].get("duplicates", {})
        examples = duplicates.get("examples", [])
        
        if not examples:
            return

        print("Moving duplicate files (keeping 1st copy)...")
        count = 0
        for group in examples:
            files = group.get("files", [])
            if len(files) > 1:
                # Keep the first one, move the rest
                for f in files[1:]:
                    file_path = Path(f).resolve()
                    self._safe_move(file_path, "duplicates")
                    count += 1
        print(f"Moved {count} extra duplicate files.")

    def _move_suspicious_files(self):
        suspicious = self.report_data["sections"].get("suspicious_samples", {})
        details = suspicious.get("details", [])
        
        if not details:
            return

        print(f"Moving {len(details)} suspicious files (low quality, empty, etc)...")
        for entry in details:
            file_path = Path(entry["file_path"]).resolve()
            self._safe_move(file_path, "suspicious")
