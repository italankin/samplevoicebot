from boto3 import session

from config import Config


class BotEnv:
    def __init__(self):
        self.config = Config()
        self.aws_session = session.Session(
            aws_access_key_id=self.config.aws.access_key_id,
            aws_secret_access_key=self.config.aws.secret_access_key,
            region_name=self.config.aws.region_name
        )


bot_env = BotEnv()
