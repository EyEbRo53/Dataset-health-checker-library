import sys
import argparse
from pathlib import Path

from dataset_health.core.dataset import DatasetTree
from dataset_health.core.pipeline import HealthCheckPipeline
from dataset_health.core.cleaner import Cleaner
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
    parser = argparse.ArgumentParser(description="Dataset Health Checker")
    parser.add_argument("folder_path", type=str, help="Path to the dataset folder")
    parser.add_argument(
        "checks", 
        type=str, 
        nargs="?", 
        help="Optional list of checks to run, e.g. '(duplicate, quality)'"
    )
    parser.add_argument("--md", action="store_true", help="Save report as Markdown")
    parser.add_argument("--json", action="store_true", help="Save report as JSON")
    parser.add_argument("--clean", action="store_true", help="Move bad files to _quarantine")
    
    args = parser.parse_args()
    
    folder_path = args.folder_path
    if not folder_path or not Path(folder_path).is_dir():
        print(f"Error: Invalid folder path: {folder_path}")
        sys.exit(1)

    tree = DatasetTree()
    root_node = tree.build_dataset_tree(folder_path)

    # --------------------------------------------
    # Select checks
    # --------------------------------------------
    selected_checks = []
    if args.checks:
        raw_arg = args.checks.strip("() ")
        selected_names = [
            name.strip().lower() for name in raw_arg.split(",") if name.strip()
        ]
        selected_checks = [
            CHECK_MAP[name] for name in selected_names if name in CHECK_MAP
        ]
        
        if not selected_checks:
            print(f"No valid checks found in '{args.checks}'. Available: {', '.join(CHECK_MAP.keys())}")
            sys.exit(1)

    if not selected_checks:
        # Default: use all
        pipeline = HealthCheckPipeline(tree)
    else:
        pipeline = HealthCheckPipeline(tree, checks=selected_checks)

    pipeline.run_all()

    # --------------------------------------------
    # Output
    # --------------------------------------------
    report_maker = pipeline.get_report()
    report_maker.print_pipeline_header()
    report_maker.render_dataset_tree(root_node)
    print(report_maker.generate_rich_report())
    
    # Save reports
    dataset_path = Path(folder_path)
    if args.md:
        md_path = dataset_path / "dataset_health_report.md"
        print(f"Saving Markdown report to {md_path}...")
        report_maker.save_report(str(md_path))
        print("Done.")

    if args.json:
        json_path = dataset_path / "dataset_health_report.json"
        print(f"Saving JSON report to {json_path}...")
        report_maker.save_report(str(json_path))
        print("Done.")

    # Clean
    if args.clean:
        cleaner = Cleaner(folder_path, report_maker.get_report())
        cleaner.clean()


if __name__ == "__main__":
    main()
