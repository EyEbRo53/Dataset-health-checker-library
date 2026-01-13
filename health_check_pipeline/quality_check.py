from .base_check import BaseCheck
from common_imports import (
    Image,
    np,
    os,
    string,
    ThreadPoolExecutor,
    ProcessPoolExecutor,
    as_completed,
)


class QualityCheck(BaseCheck):
    def penalty(self) -> int:
        """Penalty: 2 points per suspicious sample, up to 20."""
        suspicious = self.report_maker.report_data["sections"].get(
            "suspicious_samples", {}
        )
        total_suspicious = sum(
            v.get("count", 0) for k, v in suspicious.items() if k != "examples"
        )
        return min(total_suspicious * 2, 20)

    def __init__(
        self,
        dataset_tree,
        max_threads=8,
        max_processes=4,
        check_name="Quality Check",
    ):
        super().__init__(dataset_tree, check_name)

        self.max_threads = max_threads
        self.max_processes = max_processes
        self.issues = []

    # ------------------------------------------------
    # Image worker (static + picklable for multiprocessing)
    # ------------------------------------------------
    @staticmethod
    def _image_worker(file_path):
        try:
            # Downscale to reduce CPU & memory usage
            image = Image.open(file_path).convert("L").resize((64, 64))

            pixels = np.array(image)
            mean_val = np.mean(pixels)
            std_val = np.std(pixels)

            if mean_val <= 5 or mean_val >= 250:
                return (
                    file_path,
                    f"Low-quality image (mean={mean_val:.1f}, std={std_val:.1f})",
                )

        except Exception as e:
            return (file_path, f"Corrupt image: {e}")

        return None

    # ------------------------------------------------
    # Text quality checks
    # ------------------------------------------------
    def _check_text_quality(self, file_path):
        try:
            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file:
                content = file.read().strip()

            if not content:
                return (file_path, "Empty text file")

            printable_ratio = sum(char in string.printable for char in content) / max(
                len(content), 1
            )

            if printable_ratio < 0.8:
                return (file_path, "Gibberish text file")

        except Exception as e:
            return (file_path, f"Unreadable text file: {e}")

        return None

    # ------------------------------------------------
    # Dataset tree traversal
    # ------------------------------------------------
    def _collect_files(self, node):
        collected = []

        def traverse(current_node):
            if current_node.is_file:
                extension = os.path.splitext(current_node.name)[1].lower()

                if extension in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
                    collected.append((current_node.path, "image"))

                elif extension in [".txt", ".csv", ".json"]:
                    collected.append((current_node.path, "text"))
            else:
                for child in current_node.children:
                    traverse(child)

        traverse(node)
        return collected

    # ------------------------------------------------
    # Main execution
    # ------------------------------------------------
    def run(self):
        self.report_maker.start_perf_log()
        self.issues.clear()

        if not self.dataset_tree.root:
            return {"status": "No dataset tree built"}

        all_files = self._collect_files(self.dataset_tree.root)

        image_files = [file for file in all_files if file[1] == "image"]
        text_files = [file for file in all_files if file[1] == "text"]

        # -------------------
        # Threaded text checks
        # -------------------
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {
                executor.submit(self._check_text_quality, path): path
                for path, _ in text_files
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.issues.append(result)

        # ----------------------
        # Multiprocess image checks
        # ----------------------
        with ProcessPoolExecutor(max_workers=self.max_processes) as executor:
            futures = {
                executor.submit(self._image_worker, path): path
                for path, _ in image_files
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.issues.append(result)

        # -------------------
        # Report update
        # -------------------
        self.report_maker.set_suspicious_samples(self.issues)
        self.report_maker.stop_perf_log("Quality Check")

        return {
            "status": "Done",
            "issues": self.issues,
        }
