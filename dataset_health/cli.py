import sys
import os

from dataset_health.core.dataset import DatasetTree
from dataset_health.core.pipeline import HealthCheckPipeline
from dataset_health.checks.class_imbalance import ClassImbalanceCheck
from dataset_health.checks.duplicates import DuplicateCheck
from dataset_health.checks.corrupt_files import CorruptFileCheck
from dataset_health.checks.quality import QualityCheck

# ------------------------------------------------
# Available checks registry
# ------------------------------------------------
CHECK_MAP = {
    "class_imbalance": ClassImbalanceCheck,
    "duplicate": DuplicateCheck,
    "corrupt_file": CorruptFileCheck,
    "quality": QualityCheck,
}


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: dataset-health-check <folder_path> "
            "(class_imbalance, corrupt_file, duplicate, quality)"
        )
        sys.exit(1)

    folder_path = sys.argv[1]
    if not folder_path:
        print("Error: Please provide a folder path")
        sys.exit(1)

    tree = DatasetTree()
    root_node = tree.build_dataset_tree(folder_path)

    # --------------------------------------------
    # Optional: user-selected checks
    # --------------------------------------------
    if len(sys.argv) > 2:
        raw_arg = sys.argv[2].strip("() ")
        selected_names = [
            name.strip().lower() for name in raw_arg.split(",") if name.strip()
        ]

        selected_checks = [
            CHECK_MAP[name] for name in selected_names if name in CHECK_MAP
        ]

        if not selected_checks:
            print(
                f"No valid checks specified. Available: "
                f"{', '.join(CHECK_MAP.keys())}"
            )
            sys.exit(1)

        pipeline = HealthCheckPipeline(tree, checks=selected_checks)
    else:
        pipeline = HealthCheckPipeline(tree)

    pipeline.run_all()

    # --------------------------------------------
    # Output
    # --------------------------------------------
    report = pipeline.get_report()
    report.print_pipeline_header()
    report.render_dataset_tree(root_node)
    print(report.generate_rich_report())


if __name__ == "__main__":
    main()
