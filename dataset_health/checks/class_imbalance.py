from dataset_health.core.base import BaseCheck
from dataset_health.utils.common import deque


class ClassImbalanceCheck(BaseCheck):
    def penalty(self) -> int:
        """Penalty: 5 points per class with '⚠ Low Count' status."""
        classes = self.report_maker.report_data["sections"]["class_distribution"].get(
            "classes", []
        )
        low_count = sum(1 for c in classes if c.get("status") == "⚠ Low Count")
        return low_count * 5

    def __init__(self, dataset_tree):
        super().__init__(dataset_tree, "Class Imbalance Check")

    def run(self):
        self.report_maker.start_perf_log()
        counts = {}
        paths = {}
        queue = deque([(self.dataset_tree.root, [])])  # (node, path_list)

        while queue:
            node, path = queue.popleft()
            current_path = path + [node.name]

            has_subfolders = False
            file_count = 0

            for child in node.children:
                if child.is_file:
                    file_count += 1
                else:
                    has_subfolders = True
                    queue.append((child, current_path))

            if not has_subfolders and file_count > 0:
                class_key = " > ".join(current_path)
                counts[class_key] = file_count
                paths[class_key] = class_key

        total_files = sum(counts.values())
        class_distribution = []
        imbalance_ratio = None

        if total_files > 0:
            sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

            max_count = sorted_counts[0][1]
            min_count = sorted_counts[-1][1]
            imbalance_ratio = max_count / min_count if min_count > 0 else 0

            for class_path, file_count in sorted_counts:
                percentage = (file_count / total_files) * 100

                if percentage < 1:
                    status = "❌ Critical"
                elif percentage < 5:
                    status = "⚠ Low Count"
                elif percentage < 20:
                    status = "⚠ Imbalanced"
                else:
                    status = "OK"

                class_distribution.append(
                    {
                        "name": class_path.split(" > ")[-1],
                        "path": class_path,
                        "count": file_count,
                        "percentage": f"{percentage:.1f}%",
                        "status": status,
                    }
                )

        self.report_maker.set_class_distribution(class_distribution, imbalance_ratio)
        self.report_maker.stop_perf_log("Class Imbalance Check")
        return counts
