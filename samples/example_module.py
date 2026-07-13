class Greeter:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def greet(self, name: str) -> str:
        message = f"{self.prefix}, {name}"
        print(message)
        return message


def helper(value: int) -> int:
    result = value + 1
    return result


if __name__ == "__main__":
    g = Greeter("Hello")
    g.greet("PEFT")
    print(helper(3))

