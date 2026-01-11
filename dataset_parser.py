import os


class Node:
    def __init__(self, name, path, is_file=False):
        """
        Initialize a Node object.

        :param name: file or folder name
        :param path: full path
        :param is_file: a boolean indicating if it's a file
        :return: None
        """
        self.name = name
        self.path = path
        self.is_file = is_file
        self.children = []

    def add_child(self, node):
        """
        Add a child node to this node.

        :param node: child node to add
        :return: None
        """
        self.children.append(node)


class DatasetTree:
    def __init__(self):
        """
        Initialize a DatasetTree object.

        :return: None
        """
        self.root = None

    def build_dataset_tree(self, root_path):
        """
        Recursively builds a tree representing the dataset folder structure.

        :param root_path: path to the dataset folder
        :return: root Node
        """
        root_name = os.path.basename(root_path.rstrip("/\\"))
        root_node = Node(root_name, root_path, is_file=False)

        for entry in os.listdir(root_path):
            full_path = os.path.join(root_path, entry)
            if os.path.isdir(full_path):
                child_node = self._build_tree_recursive(full_path)
                root_node.add_child(child_node)
            else:
                root_node.add_child(Node(entry, full_path, is_file=True))

        self.root = root_node
        return root_node

    def _build_tree_recursive(self, root_path):
        """
        Recursively builds a tree representing the dataset folder structure.

        :param root_path: path to the dataset folder
        :return: root Node
        """
        root_name = os.path.basename(root_path.rstrip("/\\"))
        root_node = Node(root_name, root_path, is_file=False)

        for entry in os.listdir(root_path):
            full_path = os.path.join(root_path, entry)
            if os.path.isdir(full_path):
                child_node = self._build_tree_recursive(full_path)
                root_node.add_child(child_node)
            else:
                root_node.add_child(Node(entry, full_path, is_file=True))

        return root_node

    def print_tree(self, node=None, prefix=""):
        if node is None:
            node = self.root

        # check if this folder directly contains files
        has_files = any(child.is_file for child in node.children)

        print(prefix + ("|-- " if prefix else "") + node.name)

        # stop recursion if this is a leaf folder
        if has_files:
            return

        for child in node.children:
            if not child.is_file:
                self.print_tree(child, prefix + ("|   " if prefix else "    "))
