from .base_check import BaseCheck
from common_imports import hashlib, deque


class DuplicateCheck(BaseCheck):
    def penalty(self) -> int:
        """Penalty: 2 points per duplicate file, up to 20."""
        dups = self.report_maker.report_data["sections"].get("duplicates", {})
        return min(dups.get("total_duplicates", 0) * 2, 20)

    def __init__(self, dataset_tree):
        super().__init__(dataset_tree, "Duplicate Check")

    # ------------------------------------------------
    # File hashing
    # ------------------------------------------------
    def _hash_file(self, path, chunk_size=8192):
        md5 = hashlib.md5()

        with open(path, "rb") as file:
            for chunk in iter(lambda: file.read(chunk_size), b""):
                md5.update(chunk)

        return md5.hexdigest()

    # ------------------------------------------------
    # Main execution
    # ------------------------------------------------
    def run(self):
        self.report_maker.start_perf_log()

        hash_map = {}
        queue = deque([self.dataset_tree.root])

        # Breadth-first traversal of dataset tree
        while queue:
            current_node = queue.popleft()

            for child in current_node.children:
                if child.is_file:
                    file_hash = self._hash_file(child.path)
                    hash_map.setdefault(file_hash, []).append(child.path)
                else:
                    queue.append(child)

        # Keep only hashes with duplicates
        duplicate_groups = {
            file_hash: paths for file_hash, paths in hash_map.items() if len(paths) > 1
        }

        duplicates_report = {
            "groups_found": len(duplicate_groups),
            "total_duplicates": sum(
                len(paths) - 1 for paths in duplicate_groups.values()
            ),
            "examples": [],
        }

        # Report all duplicate groups
        for file_hash, paths in duplicate_groups.items():
            duplicates_report["examples"].append(
                {
                    "hash": file_hash,
                    "files": paths,
                }
            )

        self.report_maker.set_duplicates(duplicates_report)
        self.report_maker.stop_perf_log("Duplicate Check")
