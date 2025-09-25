from hippopytamus.core.annotation import (
    Controller, GetMapping, PostMapping,
    RequestParam, PathVariable, RequestBody,
    RequestMapping
)


@Controller
@RequestMapping("/h2")
class HelloController:
    # TODO: error with signature if no init specified
    def __init__(self):
        print("Hello from service!")

    # TODO: path variables
    @GetMapping("/shout/{word}")
    def shout(self, word: PathVariable(str)) -> str:
        return f"<h1>{word.upper()}!!!</h1>"

    # TODO: transforming request params to int
    @GetMapping("/add")
    def add_numbers(
        self,
        a: RequestParam(int),
        b: RequestParam(int, defaultValue=0),
    ) -> str:
        return f"<h1>Sum = {a + b}</h1>"

    # TODO: post mappings and transforming json
    @PostMapping("/echo")
    def echo_body(self, body: RequestBody(dict)) -> str:
        msg = body.get("message", "(no message)")
        return f"<h1>You said: {msg}</h1>"
