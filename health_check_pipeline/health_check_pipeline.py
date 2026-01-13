from .class_imbalance_check import ClassImbalanceCheck
from .duplicate_check import DuplicateCheck
from .corrupt_file_check import CorruptFileCheck
from .quality_check import QualityCheck

from report_maker import ReportMaker


class HealthCheckPipeline:
    def __init__(self, dataset_tree, checks=None):
        self.dataset_tree = dataset_tree

        self.checks = checks or [
            ClassImbalanceCheck,
            DuplicateCheck,
            CorruptFileCheck,
            QualityCheck,
        ]

        self.report = ReportMaker(
            "Dataset Health Check Report",
            dataset_tree.root.path,
        )

    # ------------------------------------------------
    # Run all configured checks
    # ------------------------------------------------
    def run_all(self) -> dict:
        """Run all configured checks and calculate health score."""
        total_penalty = 0
        penalties = {}
        results = {}

        for check_class in self.checks:
            check = check_class(self.dataset_tree)
            check.report_maker = self.report
            results[check_class.__name__] = check.run()
            penalty = 0
            if hasattr(check, "penalty"):
                penalty = check.penalty()
            penalties[check_class.__name__] = penalty
            total_penalty += penalty

        score = max(0, 100 - total_penalty)
        self.report.set_health_score(score, penalties)
        self.report.finalize_scan()
        return results

    def get_report(self):
        return self.report
