from .base_check import BaseCheck
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class CorruptFileCheck(BaseCheck):
    def __init__(self, dataset_tree, max_threads=8, max_processes=4):
        """
        :param dataset_tree: DatasetTree object
        :param max_threads: number of threads for lightweight file checks
        :param max_processes: number of processes for image verification
        """
        super().__init__(dataset_tree, "Corrupt File Check")
        self.max_threads = max_threads
        self.max_processes = max_processes

    def run(self):
        self.report_maker.start_perf_log()
        corrupt_files = []
        files_to_check = []

        # Flatten all files in the dataset tree
        def traverse(node):
            if node.is_file:
                files_to_check.append(node.path)
            else:
                for child in node.children:
                    traverse(child)

        traverse(self.dataset_tree.root)

        # Lightweight file check (empty/unreadable)
        def light_check(path):
            reason = None
            if os.path.getsize(path) == 0:
                reason = "empty file"
            if reason is None:
                try:
                    with open(path, "rb") as f:
                        f.read(512)
                except Exception:
                    reason = "unreadable"
            if reason:
                return {"path": path, "reason": reason}
            return None

        # Image verification (CPU-heavy)
        def image_check(path):
            try:
                with Image.open(path) as im:
                    im.verify()
            except Exception:
                return {"path": path, "reason": "image corrupted"}
            return None

        # First: run lightweight checks in threads
        non_image_files = []
        image_files = []
        for f in files_to_check:
            if PIL_AVAILABLE and f.lower().endswith(
                (".png", ".jpg", ".jpeg", ".bmp", ".gif")
            ):
                image_files.append(f)
            else:
                non_image_files.append(f)

        # Threaded light checks
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {
                executor.submit(light_check, f): f
                for f in non_image_files + image_files
            }
            intermediate_results = []
            for future in as_completed(futures):
                result = future.result()
                if result:
                    intermediate_results.append(result)

        # Separate image files that passed light check for ProcessPool
        image_files_to_verify = [
            f["path"]
            for f in intermediate_results
            if f["reason"] is None and f["path"] in image_files
        ]
        # Add files that failed light check
        corrupt_files.extend([f for f in intermediate_results if f["reason"]])

        # ProcessPool for image verification
        if PIL_AVAILABLE and image_files_to_verify:
            with ProcessPoolExecutor(max_workers=self.max_processes) as executor:
                futures = {
                    executor.submit(image_check, f): f for f in image_files_to_verify
                }
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        corrupt_files.append(result)

        # Update report
        self.report_maker.set_corrupt_files(corrupt_files)
        # print(f"Corrupt Files Found: {len(corrupt_files)}")
        self.report_maker.stop_perf_log("Corrupt File Check")
        return corrupt_files
