from hippopytamus.core.app import HippoApp
from hippopytamus.logger.logger import LoggerFactory
from hippopytamus.example.example4.components import (
        AuthorizingFilter, SecurityFilter
)

if __name__ == "__main__":
    factory = LoggerFactory.get_factory()
    factory.disable_all()
    factory.enable_for(AuthorizingFilter)
    factory.enable_for(SecurityFilter)
    app = HippoApp("hippopytamus.example.example4")
    app.run()
