from typing import Any, Callable


class Node:
    def __init__(
            self,
            field_name: str | None = None,
            left: "Node | None" = None,
            right: "Node | None" = None,
            op: str | None = None
    ):
        self.field_name = field_name
        self.left = left
        self.right = right
        self.op = op
        self.value = None


class RepoPredicate:
    def __init__(self) -> None:
        self.head: Node | None = None
        self.nodes_by_field: dict = {}

    def set_field(self, fld: str, value: Any) -> None:
        to_set = self.nodes_by_field.get(fld, [])
        for node in to_set:
            node.value = value

    def build_tree(self, fields: list) -> None:
        stack = []
        and_group = []
        node = None

        for fld, op in fields:
            node = Node(field_name=fld)
            self.nodes_by_field.setdefault(fld, []).append(node)
            and_group.append(node)

            if op == 'or' or op == '':
                if len(and_group) == 1:
                    stack.append(and_group[0])
                else:
                    temp = and_group[0]
                    for n in and_group[1:]:
                        temp = Node(left=temp, right=n, op='and')
                    stack.append(temp)
                and_group = []

        node = stack.pop(0) if stack else None
        while stack:
            node = Node(left=node, right=stack.pop(0), op='or')

        self.head = node

    def print(self, node: Node | None = None, indent: int = 0) -> None:
        if node is None:
            node = self.head
        if node is None:
            return
        prefix = "  " * indent
        if node.field_name:
            print(f"{prefix}{node.field_name} = {node.value}")
        elif node.op is not None:
            print(f"{prefix}{node.op.upper()}")
            if node.left:
                self.print(node.left, indent + 1)
            if node.right:
                self.print(node.right, indent + 1)

    def make_predicate(self, node: Node | None = None) -> Callable:
        if node is None:
            node = self.head
        if node is None:
            return None  # type: ignore
        if node.field_name:
            name = node.field_name
            return lambda entity: getattr(entity, name) == node.value
        elif node.op == 'and':
            left_pred = self.make_predicate(node.left)
            right_pred = self.make_predicate(node.right)
            return lambda entity: left_pred(entity) and right_pred(entity)
        elif node.op == 'or':
            left_pred = self.make_predicate(node.left)
            right_pred = self.make_predicate(node.right)
            return lambda entity: left_pred(entity) or right_pred(entity) 
        raise Exception("Wrong node operation")
