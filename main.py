import sys
import os

from dataset_parser import DatasetTree
from health_check_pipeline.health_check_pipeline import HealthCheckPipeline

# Ensure local imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ------------------------------------------------
# Available checks registry
# ------------------------------------------------
CHECK_MAP = {
    "class_imbalance": __import__(
        "health_check_pipeline.class_imbalance_check",
        fromlist=["ClassImbalanceCheck"],
    ).ClassImbalanceCheck,
    "duplicate": __import__(
        "health_check_pipeline.duplicate_check",
        fromlist=["DuplicateCheck"],
    ).DuplicateCheck,
    "corrupt_file": __import__(
        "health_check_pipeline.corrupt_file_check",
        fromlist=["CorruptFileCheck"],
    ).CorruptFileCheck,
    "quality": __import__(
        "health_check_pipeline.quality_check",
        fromlist=["QualityCheck"],
    ).QualityCheck,
}


def main(folder_path):
    if not folder_path:
        print("Error: Please provide a folder path")
        sys.exit(1)

    tree = DatasetTree()
    tree.build_dataset_tree(folder_path)

    print("\n" + "=" * 50)
    print("Running Health Check Pipeline...")
    print("=" * 50 + "\n")

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
    tree.print_tree()
    print(report.generate_text_report())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python3 main.py <folder_path> "
            "(class_imbalance, corrupt_file, duplicate, quality)"
        )
        sys.exit(1)

    main(sys.argv[1])
