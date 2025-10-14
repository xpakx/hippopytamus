from hippopytamus.core.annotation import Controller, GetMapping
from hippopytamus.core.annotation import Filter
from hippopytamus.core.filter import HippoFilter
from hippopytamus.logger.logger import LoggerFactory


@Controller
class MyService:
    @GetMapping("/secured")
    def test(self) -> str:
        return "secret"


@Filter(priority=9999)
class SecurityFilter(HippoFilter):
    def __init__(self):
        self.logger = LoggerFactory.get_logger()

    def filter(self, request, context) -> bool:
        self.logger.log("Securing", request=request, context=context)
        return not context.get('authorized', False)


@Filter
class AuthorizingFilter(HippoFilter):
    def __init__(self):
        self.logger = LoggerFactory.get_logger()

    def filter(self, request, context) -> bool:
        self.logger.log("Authorizing")
        auth = context.get('params', {}).get('auth')
        if auth is not None and len(auth) == 1 and auth[0] == "secret":
            context['authorized'] = True
        return False
