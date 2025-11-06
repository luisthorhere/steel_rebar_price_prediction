from pydantic_settings import BaseSettings
from pydantic import Field, AliasPath
from pathlib import Path
import yaml
from logger.logger import logger

class YamlConfiguration:
    def __init__(self):
        config = self.load_file(Path(__file__).parent.resolve() / "config.yml")
       
        self.config  = config 

        logger.info("Configuration file loaded")

    def load_file(self, file_name) -> dict:
        if not file_name.exists():
            raise FileNotFoundError(f"File not found: {file_name.as_posix()}")

        with open(file_name, encoding="utf-8") as fp:
            file: dict = yaml.load(fp, Loader=yaml.FullLoader)

        if file is None:
            return {}

        return file

cfg_yaml = YamlConfiguration()

class Settings(BaseSettings):
    api_key: list = Field(validation_alias=AliasPath("api_key"))
    rate_limit: int = Field(validation_alias=AliasPath("rate_limit"))

SETTINGS =  Settings(**cfg_yaml.config)