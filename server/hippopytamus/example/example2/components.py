from hippopytamus.core.annotation import Component


# TODO: cycle detection
@Component
class A:
    # TODO: string type hints ????
    def __init__(self, b: "B"):
        self.b = b


@Component
class B:
    def __init__(self, a: A):
        self.a = a
