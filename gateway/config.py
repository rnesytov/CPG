import os

from logging.config import dictConfig
from pathlib import Path
from attrdict import AttrDict
from attrdict.merge import merge
from electrumx.lib.coins import Coin
from gateway.utils import read_yaml


class ConfigurationNotFound(Exception):
    pass


class Configuration(AttrDict):
    PROJ_ROOT = Path(__file__).parent.parent
    DEFAULT_PATH = PROJ_ROOT / 'config' / 'cpg_configuration_default.yml'
    LOCAL_PATH = PROJ_ROOT / 'config' / 'cpg_configuration.yml'
    EXTERNAL_PATH = Path('%s/cpg_configuration.yml' % os.environ.get('CPG_CONFIG_PATH'))

    @classmethod
    def load(cls, path=''):
        arg_path = Path(path)
        default_config = read_yaml(cls.DEFAULT_PATH)

        custom_config_path = arg_path.is_file() and arg_path or cls.EXTERNAL_PATH.is_file() and \
                             cls.EXTERNAL_PATH or cls.LOCAL_PATH.is_file() and cls.LOCAL_PATH  # noqa: E127

        if not custom_config_path:
            raise ConfigurationNotFound('You missed a local config in config/ directory '
                                        'or did not specified CPG_CONFIG_PATH environment variable')

        custom_config = read_yaml(custom_config_path) or {}

        return cls(merge(default_config, custom_config))

    @property
    def coin_class(self):
        return Coin.lookup_coin_class(self.coin, self.net)

    @property
    def scheduler_paused(self):
        return not self.job_settings.scheduler_enabled

    def for_job(self, job_name):
        return getattr(self.job_settings, job_name)

    def setup_logging(self):
        dictConfig(self.logging)

    def __repr__(self):
        contents = dict.__repr__(self)

        return f'Configuration({contents})'
