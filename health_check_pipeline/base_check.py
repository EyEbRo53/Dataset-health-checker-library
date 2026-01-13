class BaseCheck:
    def __init__(self, dataset_tree, check_name=None):
        """
        Initialize a BaseCheck object.

        :param dataset_tree: the dataset tree to check
        :param check_name: name of the check (used for report)
        :return: None
        """

        self.dataset_tree = dataset_tree
        self.check_name = check_name or self.__class__.__name__
        self.report_maker = None

    def run(self):
        """
        Run the check and return a result dict.

        :return: result dictionary
        """
        raise NotImplementedError("Each check must implement the run method.")

    def penalty(self) -> int:
        """Return the penalty for this check (default 0). Override in subclasses."""
        return 0
