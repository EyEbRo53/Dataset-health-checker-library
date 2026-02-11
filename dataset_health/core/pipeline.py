from typing import List, Type, Dict, Any

from dataset_health.checks.class_imbalance import ClassImbalanceCheck
from dataset_health.checks.duplicates import DuplicateCheck
from dataset_health.checks.corrupt_files import CorruptFileCheck
from dataset_health.checks.quality import QualityCheck

from dataset_health.core.report import ReportMaker
from dataset_health.core.dataset import DatasetTree
from dataset_health.core.base import BaseCheck


class HealthCheckPipeline:
    def __init__(self, dataset_tree: DatasetTree, checks: List[Type[BaseCheck]] = None):
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

    def add_check(self, check_class: Type[BaseCheck]):
        """Register a new check class to the pipeline."""
        if check_class not in self.checks:
            self.checks.append(check_class)


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
