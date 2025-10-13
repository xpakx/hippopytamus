from hippopytamus.core.annotation import (
    Controller, GetMapping, PostMapping,
    RequestParam, PathVariable, RequestBody,
    RequestMapping
)


@Controller
@RequestMapping("/h2")
class HelloController:
    @GetMapping("/shout/{word}")
    def shout(self, word: PathVariable(str)) -> str:
        return f"<h1>{word.upper()}!!!</h1>"

    @GetMapping("/add")
    def add_numbers(
        self,
        a: RequestParam(int),
        b: RequestParam(int, defaultValue=0),
    ) -> str:
        return f"<h1>Sum = {a + b}</h1>"

    @GetMapping("/concat")
    def concat_numbers(
        self,
        a: RequestParam(str),
        b: RequestParam(str, defaultValue='0'),
    ) -> str:
        return f"<h1>Sum = {a + b}</h1>"

    @PostMapping("/echo")
    def echo_body(self, body: RequestBody(dict)) -> str:
        msg = body.get("message", "(no message)")
        return f"<h1>You said: {msg}</h1>"

    @PostMapping("/echostr")
    def echo_str(self, msg: RequestBody(str)) -> str:
        return f"<h1>You said: {msg}</h1>"
