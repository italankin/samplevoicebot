from boto3 import session

from config import Config
from util.statistics import Statistics


class BotEnv:
    def __init__(self):
        self.config = Config()
        self.aws_session = session.Session(
            aws_access_key_id=self.config.aws.access_key_id,
            aws_secret_access_key=self.config.aws.secret_access_key,
            region_name=self.config.aws.region_name
        )
        self.statistics = Statistics()


bot_env = BotEnv()
