from hippopytamus.core.app import HippoApp
from hippopytamus.core.container import HippoContainer
from hippopytamus.core.exception import HippoExceptionManager
from hippopytamus.logger.logger import LoggerFactory

if __name__ == "__main__":
    factory = LoggerFactory.get_factory()
    factory.disable_all()
    factory.enable_for(HippoContainer)
    factory.enable_for(HippoExceptionManager)
    app = HippoApp("hippopytamus.example.example3")
    app.run()
