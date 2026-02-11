import json
from datetime import datetime
import time
import tracemalloc

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from rich.align import Align


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

        suspicious["examples"] = examples[:5]  # store first 5 examples only for display
        
        # Store full details for JSON and cleaning
        suspicious["details"] = [{"file_path": f, "issue": i} for f, i in issues]
        
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

    # ------------------------------------------------------------------
    # Text Report Rendering
    # ------------------------------------------------------------------

    def _generate_full_text(self) -> str:
        """Generates a detailed text report with ALL findings."""
        r = self.report_data
        s = r["sections"]
        out = []

        def line(text=""):
            out.append(text)

        def divider():
            out.append("-" * 50)

        line("=" * 50)
        line("DATASET HEALTH CHECK REPORT (DETAILED)")
        line("=" * 50)
        line(f"Date: {r['created_at']}")
        if r["dataset_path"]:
            line(f"Dataset Path: {r['dataset_path']}")
        line()

        # Summary
        if s["summary"]:
            line("SCAN SUMMARY")
            divider()
            for k, v in s["summary"].items():
                line(f"{k.replace('_', ' ').title():<25} : {v}")
            line()

        # Class Distribution
        classes = s["class_distribution"]["classes"]
        if classes:
            line("CLASS DISTRIBUTION")
            divider()
            for c in classes:
                pct = c.get("percentage", "0%")
                line(f"{c.get('name', 'N/A'):<30} | {c.get('count', 0):<10} | {pct:<10} | {c.get('status', 'OK')}")
            
            ratio = s["class_distribution"].get("imbalance_ratio")
            if ratio is not None:
                line(f"\nImbalance Ratio: {ratio:.2f}")
            line()

        # Duplicates
        dup = s.get("duplicates")
        if dup:
            line("DUPLICATE FILES")
            divider()
            line(f"Groups: {dup.get('groups_found', 0)}")
            line(f"Total Duplicates: {dup.get('total_duplicates', 0)}")
            
            examples = dup.get("examples", [])
            if examples:
                line("\nAll Duplicate Groups:")
                for idx, ex in enumerate(examples, 1):
                    line(f"\nGroup {idx} (Hash: {ex.get('hash', 'N/A')}):")
                    for f in ex.get("files", []):
                        line(f"  - {f}")
            line()

        # Corrupt files
        corrupt = s.get("corrupt_files")
        if corrupt:
            line("CORRUPT FILES")
            divider()
            line(f"Total: {len(corrupt)}")
            for f in corrupt:
                line(f"  - {f['file_path']} ({f['reason']})")
            line()

        # Suspicious samples
        suspicious = s.get("suspicious_samples")
        if suspicious:
            line("SUSPICIOUS SAMPLES")
            divider()
            for k, v in suspicious.items():
                if k == "examples": continue
                line(f"{k.replace('_', ' ').title():<25} : {v.get('count', 0)}")
            
            examples = suspicious.get("examples", [])
            if examples:
                line("\nAll Suspicious Samples:")
                for e in examples:
                    line(f"  - {e}")
            line()

        # Score
        line("HEALTH SCORE")
        divider()
        line(f"Score: {r['health_score']['score']} / 100")
        
        return "\n".join(out)

    # ------------------------------------------------------------------
    # Markdown Report Rendering
    # ------------------------------------------------------------------

    def _generate_full_markdown(self) -> str:
        """Generates a detailed, pretty markdown report."""
        r = self.report_data
        s = r["sections"]
        out = []

        def line(text=""):
            out.append(text)

        # Title
        line(f"# Dataset Health Check Report")
        line(f"> **Date:** {r['created_at']}  ")
        line(f"> **Dataset:** `{r['dataset_path']}`  ")
        line()

        # Score formatted nicely
        score = r["health_score"]["score"]
        status = "✅ Healthy" if score >= 80 else "⚠ Needs Attention" if score >= 50 else "❌ Critical"
        line(f"## Overall Health Score: {score} / 100")
        line(f"**Status:** {status}")
        line()

        # Summary Table
        if s["summary"]:
            line("## Scan Summary")
            line("| Metric | Value |")
            line("|:---|:---|")
            for k, v in s["summary"].items():
                line(f"| {k.replace('_', ' ').title()} | {v} |")
            line()

        # Class Distribution Table
        classes = s["class_distribution"]["classes"]
        if classes:
            line("## Class Distribution")
            line("| Class Name | Images | Percentage | Status |")
            line("|:---|---:|---:|:---|")
            for c in classes:
                line(f"| {c.get('name')} | {c.get('count')} | {c.get('percentage')} | {c.get('status')} |")
            
            ratio = s["class_distribution"].get("imbalance_ratio")
            if ratio:
                line(f"\n**Imbalance Ratio:** {ratio:.2f}")
            line()

        # Duplicates
        dup = s.get("duplicates")
        if dup and dup.get("examples"):
            line("## Duplicate Files")
            line(f"- **Total Duplicates:** {dup.get('total_duplicates', 0)}")
            line(f"- **Duplicate Groups:** {dup.get('groups_found', 0)}")
            line()
            
            line("### Examples")
            for idx, ex in enumerate(dup["examples"], 1):
                line(f"#### Group {idx} (Hash: `{ex.get('hash')}`)")
                for f in ex.get("files", []):
                    line(f"- `{f}`")
            line()

        # Corrupt Files
        corrupt = s.get("corrupt_files")
        if corrupt:
            line("## Corrupt Files")
            line(f"**Total Found:** {len(corrupt)}")
            line()
            line("| File Path | Reason |")
            line("|:---|:---|")
            for f in corrupt:
                line(f"| `{f['file_path']}` | {f['reason']} |")
            line()

        # Suspicious Samples
        suspicious = s.get("suspicious_samples")
        if suspicious:
            line("## Suspicious Samples")
            line("| Issue Type | Count |")
            line("|:---|---:|")
            for k, v in suspicious.items():
                if k in ["examples", "details"]: continue
                line(f"| {k.replace('_', ' ').title()} | {v.get('count', 0)} |")
            line()
            
            details = suspicious.get("details", [])
            if details:
                line("### All Issues")
                line("| File Path | Issue |")
                line("|:---|:---|")
                for d in details:
                    line(f"| `{d['file_path']}` | {d['issue']} |")
            line()

        # Recommendations
        recs = s.get("recommendations")
        if recs:
            line("## Recommendations")
            for i, r_text in enumerate(recs, 1):
                line(f"{i}. {r_text}")
            line()
            
        # Performance Log
        if self._perf_log:
            line("## Performance Log")
            line("| Task | Duration (sec) | Peak Memory (MB) |")
            line("|:---|---:|---:|")
            for entry in self._perf_log:
                line(f"| {entry['task']} | {entry['duration_sec']:.4f} | {entry['memory_peak_mb']:.2f} |")
            line()

        return "\n".join(out)

    def save_report(self, file_path: str):
        """Saves the report to the specified file path."""
        if file_path.endswith(".json"):
            self.save_to_json(file_path)
        elif file_path.endswith(".md"):
            content = self._generate_full_markdown()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            # Default to text
            content = self._generate_full_text()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)


    #
    # Rich Report Rendering
    #
    def print_pipeline_header(self, title="Health Check Report"):
        """
        Prints a fancy header for pipeline sections using Rich.

        :param title: The title text to display
        """

        console = Console()

        panel = Panel(
            Align.center(f"[bold green]{title}[/bold green]", vertical="middle"),
            border_style="bright_blue",
            padding=(1, 4),
            expand=True,
        )
        console.print(panel)

    def render_dataset_tree(self, root_node):
        """
        Render a dataset tree using Rich.

        :param root_node: root Node of the DatasetTree
        """
        console = Console()

        def add_node(rich_tree, node):
            # check if this folder directly contains files
            has_files = any(child.is_file for child in node.children)

            # add this node to the Rich tree
            branch = rich_tree.add(node.name)

            # stop recursion if folder directly contains files
            if has_files:
                return

            for child in node.children:
                if not child.is_file:
                    add_node(branch, child)

        rich_tree = Tree(f"[bold blue]{root_node.name}[/bold blue]")
        add_node(rich_tree, root_node)
        console.print(rich_tree)

    def generate_rich_report(self):
        console = Console()
        r = self.report_data
        s = r["sections"]

        # Header
        console.rule("[bold cyan]DATASET HEALTH CHECK[/bold cyan]")

        # Dataset Path
        if r["dataset_path"]:
            console.print(f"[bold]Dataset Path:[/bold] {r['dataset_path']}\n")

        # Summary
        if s["summary"]:
            console.print(Panel.fit("[bold green]Scan Summary[/bold green]"))
            for k, v in s["summary"].items():
                console.print(f"[green]{k.replace('_', ' ').title():<25}[/green] : {v}")
            console.print()

        # Class Distribution Tree
        classes = s["class_distribution"]["classes"]
        if classes:
            console.rule("[bold magenta]CLASS DISTRIBUTION[/bold magenta]")

            tree = Tree("[bold]Dataset Classes[/bold]")
            for c in classes:
                pct = c.get("percentage", 0)
                try:
                    pct_val = float(pct)
                except (ValueError, TypeError):
                    pct_val = 0.0
                node_text = f"{c.get('name', 'N/A')} ({c.get('count', 0)} images, {pct_val:.1f}%) [{c.get('status', 'OK')}]"
                tree.add(node_text)
            console.print(tree)
            console.print()

            # Table
            table = Table(title="Class Distribution Details")
            table.add_column("Class Name", style="cyan")
            table.add_column("Images", justify="right")
            table.add_column("Percentage", justify="right")
            table.add_column("Status", style="magenta")

            for c in classes:
                # Ensure percentage is a float
                pct = c.get("percentage", 0)
                try:
                    pct_val = float(
                        str(pct).replace("%", "")
                    )  # Remove % if it's a string
                except (ValueError, TypeError):
                    pct_val = 0.0

                table.add_row(
                    c.get("name", "N/A"),
                    str(c.get("count", 0)),
                    f"{pct_val:.1f}%",
                    c.get("status", "OK"),
                )

            console.print(table)

            ratio = s["class_distribution"].get("imbalance_ratio")
            if ratio is not None:
                console.print(
                    f"\n[bold yellow]Imbalance Ratio (Max / Min):[/bold yellow] {ratio:.2f}"
                )
            console.print()

        # Duplicates
        dup = s.get("duplicates")
        if dup:
            console.rule("[bold red]DUPLICATE FILES[/bold red]")
            console.print(f"Duplicate Groups Found: {dup.get('groups_found', 0)}")
            console.print(f"Total Duplicate Files : {dup.get('total_duplicates', 0)}\n")

            examples = dup.get("examples", [])
            for idx, ex in enumerate(examples[:5], start=1):
                panel_text = (
                    f"[bold]Group {idx}[/bold]\nHash: {ex.get('hash', 'N/A')}\nFiles:\n"
                    + "\n".join(f"  - {f}" for f in ex.get("files", []))
                )
                console.print(Panel(panel_text, style="red"))

        # Corrupt files
        corrupt = s.get("corrupt_files", [])
        if corrupt:
            console.rule("[bold red]CORRUPT FILES[/bold red]")
            console.print(f"Corrupt Files Found: {len(corrupt)}\n")
            for f in corrupt:
                console.print(f"  - [red]{f['file_path']}[/red] ({f['reason']})")
            console.print()

        # Suspicious samples
        suspicious = s.get("suspicious_samples")
        if suspicious:
            console.rule("[bold yellow]SUSPICIOUS SAMPLES[/bold yellow]")
            for k, v in suspicious.items():
                if k in ["examples", "details"]:
                    continue
                console.print(
                    f"[yellow]{k.replace('_', ' ').title():<25}[/yellow] : {v.get('count', 0)}"
                )

            examples = suspicious.get("examples")
            if examples:
                console.print("\nExample Issues:")
                for e in examples[:5]:
                    console.print(f"  - {e}")
            console.print()

        # Recommendations
        recs = s.get("recommendations")
        if recs:
            console.rule("[bold cyan]RECOMMENDATIONS[/bold cyan]")
            for i, r_text in enumerate(recs, 1):
                console.print(f"{i}. {r_text}")
            console.print()

        # Health score
        console.rule("[bold green]OVERALL DATASET HEALTH SCORE[/bold green]")
        score = r["health_score"]["score"]
        status_color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
        status_text = (
            "✓ Healthy"
            if score >= 80
            else "⚠ Needs Attention" if score >= 50 else "❌ Critical"
        )
        console.print(
            f"Score : [bold {status_color}]{score}[/bold {status_color}] / 100"
        )
        console.print(
            f"Status: [bold {status_color}]{status_text}[/bold {status_color}]\n"
        )

        # Performance log
        if self._perf_log:
            console.rule("[bold blue]PERFORMANCE LOG[/bold blue]")
            for entry in self._perf_log:
                console.print(
                    f"[cyan]{entry['task']:<30}[/cyan] : {entry['duration_sec']:.4f} sec, {entry['memory_peak_mb']:.2f} MB peak"
                )
            console.print()

        console.rule("[bold cyan]END OF REPORT[/bold cyan]")

    def save_text_report(self, file_path: str):
        with open(file_path, "w") as f:
            f.write(self.generate_text_report())
