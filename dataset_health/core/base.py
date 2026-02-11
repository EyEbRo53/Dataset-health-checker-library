import abc
from typing import Dict, Any, Optional
from .report import ReportMaker
from .dataset import DatasetTree

class BaseCheck(abc.ABC):
    """
    Abstract base class for all dataset health checks.
    """
    def __init__(self, dataset_tree: DatasetTree, check_name: Optional[str] = None):
        """
        Initialize a BaseCheck object.

        :param dataset_tree: the dataset tree to check
        :param check_name: name of the check (used for report)
        """
        self.dataset_tree = dataset_tree
        self.check_name = check_name or self.__class__.__name__
        self.report_maker: Optional[ReportMaker] = None

    @abc.abstractmethod
    def run(self) -> Dict[str, Any]:
        """
        Run the check and return a result dict.

        :return: result dictionary
        """
        pass

    def penalty(self) -> int:
        """
        Return the penalty for this check (default 0).
        Override in subclasses to calculate penalty based on findings.
        
        :return: penalty score (0-100)
        """
        return 0

