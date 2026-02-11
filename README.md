# Dataset Health Checker

## Overview

Dataset Health Checker is a lightweight Python library designed to quickly scan and diagnose common issues in machine learning datasets organized in folders (e.g., Kaggle-style class folders). Unlike heavy enterprise tools, it is zero-config, folder-based, and easy to use—just point it at your dataset and get an instant, readable report.

## Problem

Machine learning datasets are often messy: class imbalance, data leakage, duplicates, corrupt files, and mislabeled folders are common. Existing tools are either too generic, require extensive setup, or are overkill for simple dataset validation.

## Features

- **Class Imbalance Detection**: Reports if some classes have far fewer samples than others.
- **Duplicate Finder**: Uses file hashing to find exact copies of images/files that waste space or bias training.
- **Corrupt File Detection**: Flags files that cannot be opened (e.g., broken images).
- **Quality Scorer**: Flags suspicious samples (e.g., very small, very dark, empty, or gibberish files).
- **Readable Report**: Outputs a clean, human-friendly summary of all issues found.
- **Zero-Config**: No need to write code or configure settings—just run and get results.
- **Optional Bad Batch Mover**: With a flag (e.g., `--clean`), automatically moves problematic files to a `_quarantine/` folder for easy inspection.

## Why It's Different

- **Lightweight & Fast**: No heavy dependencies or complex setup.
- **Dataset-First**: Works directly on folder-based datasets.
- **Universal Need**: Useful for anyone working with computer vision or tabular ML data.
- **High Portability**: Can be integrated into CI/CD pipelines or used as a GitHub Action.

## Core Technologies

- **PIL**: For image loading and corruption checks.
- **OpenCV**: (optional) For advanced image analysis.
- **hashlib**: For duplicate detection via file hashes.
- **numpy**: For statistical analysis of image quality.

## How It Works

The Health Check Pipeline includes:

- **Duplicate Finder**: Uses MD5/SHA hashing to find exact file copies.
- **Class Imbalance**: Counts files per class folder to highlight imbalance.
- **Visual Corruption**: Opens images with PIL to catch unreadable files.
- **Quality Scorer**: Uses numpy to flag images that are all black/white or have suspicious stats.

## Usage

```bash
from dataset_health import DatasetTree, HealthCheckPipeline, BaseCheck

# 1. Build dataset tree
tree = DatasetTree()
root = tree.build_dataset_tree("/path/to/dataset")

# 2. Initialize pipeline
pipeline = HealthCheckPipeline(tree)

# 3. Add custom check (Optional)
class MyCustomCheck(BaseCheck):
    def run(self):
        return {"status": "Passed"}

pipeline.add_check(MyCustomCheck)

# 4. Run checks
results = pipeline.run_all()

# 5. Generate report
report = pipeline.get_report()
print(report.generate_rich_report())

```

running directly from folder:
```bash
python3 main.py /path/to/dataset
```

running as a package
```bash
dataset-health-check /path/to/dataset
```

## Running Specific Checks

You can choose to run only specific checks instead of the full suite.

### Via CLI

Pass the check names as a comma-separated list (parentheses optional):

```bash
# Run only duplicate and quality checks
dataset-health-check /path/to/dataset "(duplicate, quality)"
```

**Available checks:** `class_imbalance`, `duplicate`, `corrupt_file`, `quality`

### Via Code

Pass the list of check classes to the pipeline:

```python
from dataset_health import DatasetTree, HealthCheckPipeline
from dataset_health.checks.duplicates import DuplicateCheck

tree = DatasetTree()
tree.build_dataset_tree("/path/to/dataset")

# Run ONLY the duplicate check
pipeline = HealthCheckPipeline(tree, checks=[DuplicateCheck])
pipeline.run_all()
```

## Potential Killer Feature

- **Bad Batch Mover**: Add a `--clean` flag to automatically move flagged files to a `_quarantine/` folder for review.

## License

MIT

## Contributing

Pull requests and suggestions are welcome!
