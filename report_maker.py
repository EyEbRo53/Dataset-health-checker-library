import json
from datetime import datetime
import time
import tracemalloc


class ReportMaker:
    """
    Creates, manages, and exports dataset health reports.
    """

    def __init__(self, report_name: str, dataset_path: str | None = None):
        self.report_name = report_name
        self.dataset_path = dataset_path
        self.scan_start_time = datetime.now()
        self._perf_log = []  # Stores (task_name, duration, memory_used)

        self.report_data = {
            "name": report_name,
            "dataset_path": dataset_path,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "sections": {
                "summary": {},
                "class_distribution": {
                    "classes": [],
                    "imbalance_ratio": None,
                },
                "duplicates": {},
                "corrupt_files": [],
                "suspicious_samples": {},
                "recommendations": [],
            },
            "health_score": {
                "score": 0,
                "penalties": {},
            },
        }

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    def _update_timestamp(self):
        self.report_data["last_updated"] = datetime.now().isoformat()

    def finalize_scan(self):
        """
        Finalize scan timing and store scan duration.
        """
        duration = datetime.now() - self.scan_start_time
        self.report_data["sections"]["summary"]["scan_duration"] = str(duration)
        self._update_timestamp()

    # ------------------------------------------------------------------
    # Section setters
    # ------------------------------------------------------------------

    def set_summary(self, summary: dict):
        self.report_data["sections"]["summary"].update(summary)
        self._update_timestamp()

    def set_class_distribution(
        self, classes: list[dict], imbalance_ratio: float | None
    ):
        self.report_data["sections"]["class_distribution"] = {
            "classes": classes,
            "imbalance_ratio": imbalance_ratio,
        }
        self._update_timestamp()

    def set_duplicates(self, duplicates: dict):
        """
        Expected keys:
        - groups_found
        - total_duplicates
        - examples
        """
        self.report_data["sections"]["duplicates"] = duplicates
        self._update_timestamp()

    def set_corrupt_files(self, corrupt_files: list[dict]):
        """
        Each item:
        - file_path
        - reason
        """
        self.report_data["sections"]["corrupt_files"] = corrupt_files
        self._update_timestamp()

    def set_suspicious_samples(self, issues: list[tuple[str, str]]):
        """
        Accepts a list of issues from QualityCheck.
        Converts it into a structured report section.

        Example input:
        [
            ("images/img1.jpg", "Low-quality image (mean=2.1, std=0.5)"),
            ("texts/file1.txt", "Empty text file")
        ]
        """
        suspicious = {}
        examples = []

        for file_path, issue in issues:
            examples.append(f"{file_path} ({issue})")

            # Categorize by issue type (e.g., very_dark, very_small, empty, gibberish)
            key = None
            if "Low-quality image" in issue:
                if "mean=" in issue:
                    mean_val = float(issue.split("mean=")[1].split(",")[0])
                    key = (
                        "very_dark"
                        if mean_val <= 5
                        else "very_bright" if mean_val >= 250 else "low_quality"
                    )
            elif "Empty text file" in issue:
                key = "empty_text"
            elif "Gibberish text file" in issue:
                key = "gibberish_text"
            else:
                key = "other_issues"

            if key not in suspicious:
                suspicious[key] = {"count": 0}
            suspicious[key]["count"] += 1

        suspicious["examples"] = examples[:5]  # store first 5 examples only
        self.report_data["sections"]["suspicious_samples"] = suspicious
        self._update_timestamp()

    def set_recommendations(self, recommendations: list[str]):
        self.report_data["sections"]["recommendations"] = recommendations
        self._update_timestamp()

    def add_recommendation(self, text: str):
        self.report_data["sections"]["recommendations"].append(text)
        self._update_timestamp()

    def set_health_score(self, score: int, penalties: dict | None = None):
        self.report_data["health_score"]["score"] = max(0, min(100, score))
        if penalties:
            self.report_data["health_score"]["penalties"] = penalties
        self._update_timestamp()

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def get_report(self) -> dict:
        return self.report_data

    def save_to_json(self, file_path: str):
        with open(file_path, "w") as f:
            json.dump(self.report_data, f, indent=2)

    #
    # Logging
    #
    def start_perf_log(self):
        """
        Start measuring memory and time for a task.
        """
        self._perf_start_time = time.perf_counter()
        tracemalloc.start()

    def stop_perf_log(self, task_name: str):
        """
        Stop measuring and store duration and memory used.
        """
        duration = time.perf_counter() - self._perf_start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._perf_log.append(
            {
                "task": task_name,
                "duration_sec": duration,
                "memory_peak_mb": peak / 1024 / 1024,
            }
        )

    # ------------------------------------------------------------------
    # Text Report Rendering
    # ------------------------------------------------------------------
    # At the end, append performance log to logs.txt

    def append_performance_log_to_file(self):
        """
        Appends the performance log to logs.txt in the required format.
        """
        if not self._perf_log:
            return
        duration = self.report_data["sections"]["summary"].get("scan_duration", "N/A")
        lines = []
        lines.append(f"Scan Duration             : {duration}")
        lines.append("--------------------------------------------------")
        lines.append("PERFORMANCE LOG")
        lines.append("--------------------------------------------------")
        for entry in self._perf_log:
            lines.append(
                f"{entry['task']:<30} : {entry['duration_sec']:.4f} sec, {entry['memory_peak_mb']:.2f} MB peak"
            )
        lines.append("")
        with open("logs.txt", "a") as f:
            f.write("\n".join(lines) + "\n")

    def generate_text_report(self) -> str:

        r = self.report_data
        s = r["sections"]
        # print(self.report_data["sections"])

        out = []

        def line(text=""):
            out.append(text)

        def divider():
            out.append("-" * 50)

        line("=" * 50)
        line("DATASET HEALTH CHECK REPORT")
        line("=" * 50)
        line()

        if r["dataset_path"]:
            line("Dataset Path:")
            line(f"  {r['dataset_path']}")
            line()

        # Summary
        if s["summary"]:
            line("Scan Summary:")
            for k, v in s["summary"].items():
                line(f"  {k.replace('_', ' ').title():<25} : {v}")
            line()

        # Class Distribution
        classes = s["class_distribution"]["classes"]
        if classes is not None:
            divider()
            line("CLASS DISTRIBUTION")
            divider()

            # Build tree structure from all paths
            tree = {}
            for c in classes:
                if c.get("path"):
                    path_parts = c.get("path").split(" > ")
                    current = tree
                    for i, part in enumerate(path_parts):
                        if part not in current:
                            current[part] = {}
                        current = current[part]

            # Render tree
            def render_tree(node, indent=0):
                for i, (key, subtree) in enumerate(node.items()):
                    is_last = i == len(node) - 1
                    prefix = "|-- " if indent > 0 else ""
                    line("    " * indent + prefix + key)
                    if subtree:
                        render_tree(subtree, indent + 1)

            if tree:
                render_tree(tree)
            line()

            # Then show table
            divider()
            line(f"{'Class Name':<20} {'Images':<12} {'Percentage':<12} {'Status':<15}")
            divider()
            for c in classes:
                pct = c.get("percentage", 0)
                if isinstance(pct, (int, float)):
                    pct = f"{pct:.1f}%"
                line(
                    f"{c.get('name', 'N/A'):<20} "
                    f"{c.get('count', 0):<12} "
                    f"{pct:<12} "
                    f"{c.get('status', 'OK'):<15}"
                )

            ratio = s["class_distribution"].get("imbalance_ratio")
            if ratio is not None:
                line()
                line(f"Imbalance Ratio (Max / Min): {ratio:.2f}")
            line()

        # Duplicates
        dup = s["duplicates"]
        if dup is not None:
            divider()
            line("DUPLICATE FILES")
            divider()
            line(f"Duplicate Groups Found: {dup.get('groups_found', 0)}")
            line(f"Total Duplicate Files : {dup.get('total_duplicates', 0)}")

            examples = dup.get("examples", [])
            if examples:
                line()
                line("Duplicate Groups (showing up to 5 examples):")
                for idx, ex in enumerate(examples[:5], start=1):  # show only first 5
                    line(f"\n  Group {idx}:")
                    line(f"    Hash: {ex.get('hash', 'N/A')}")
                    line("    Files:")
                    for f in ex.get("files", []):
                        line(f"      - {f}")
            line()

        # Corrupt files
        corrupt = s["corrupt_files"]
        if corrupt is not None:
            divider()
            line("CORRUPT FILES")
            divider()
            line(f"Corrupt Files Found: {len(corrupt)}")
            line()
            if corrupt:
                line("Corrupt files:")
                for f in corrupt:
                    line(f"  - {f['file_path']} ({f['reason']})")
                line()

        # Suspicious samples
        suspicious = s["suspicious_samples"]
        if suspicious:
            divider()
            line("SUSPICIOUS SAMPLES")
            divider()
            for k, v in suspicious.items():
                if k == "examples":
                    continue
                line(f"{k.replace('_', ' ').title():<25} : {v.get('count', 0)}")
            examples = suspicious.get("examples")
            if examples:
                line()
                line("Example Issues:")
                for e in examples[:5]:
                    line(f"  - {e}")
            line()

        # Recommendations
        recs = s["recommendations"]
        if recs:
            divider()
            line("RECOMMENDATIONS")
            divider()
            for i, r in enumerate(recs, 1):
                line(f"{i}. {r}")
            line()

        # Health score
        divider()
        line("OVERALL DATASET HEALTH SCORE")
        divider()
        score = r["health_score"]["score"]
        status = (
            "✓ Healthy"
            if score >= 80
            else "⚠ Needs Attention" if score >= 50 else "❌ Critical"
        )
        line(f"Score: {score} / 100")
        line(f"Status: {status}")
        line()

        # add logs
        if self._perf_log:
            divider()
            line("PERFORMANCE LOG")
            divider()
            for entry in self._perf_log:
                line(
                    f"{entry['task']:<30} : "
                    f"{entry['duration_sec']:.4f} sec, "
                    f"{entry['memory_peak_mb']:.2f} MB peak"
                )
            line()
            self.append_performance_log_to_file()

        line("=" * 50)
        line("END OF REPORT")
        line("=" * 50)

        return "\n".join(out)

    def save_text_report(self, file_path: str):
        with open(file_path, "w") as f:
            f.write(self.generate_text_report())
