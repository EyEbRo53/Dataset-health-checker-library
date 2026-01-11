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
python3 main.py <dataset_folder> (class_imbalance, corrupt_file, duplicate, quality)
```

- Specify which checks to run as a comma-separated list in parentheses.
- If no checks are specified, all are run by default.

## Example

```bash
python3 main.py ./my_data (class_imbalance, duplicate)
```

## Potential Killer Feature

- **Bad Batch Mover**: Add a `--clean` flag to automatically move flagged files to a `_quarantine/` folder for review.

## License

MIT

## Contributing

Pull requests and suggestions are welcome!
