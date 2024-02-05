import os
import yaml

from dataclasses import dataclass, field, fields
from collections.abc import Mapping

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(THIS_DIR, "conf/default_config.yaml")


@dataclass
class Config:
    RUN: dict = field(default_factory=dict)
    ENV: dict = field(default_factory=dict)

    def get_defaults(self):
        with open(DEFAULT_CONFIG_PATH) as file_stream:
            return {
                k: (v if v is not None else {})
                for (k, v) in yaml.safe_load(file_stream).items()
            }

    def reset(self):
        """
        Clear all configuration data and load defaults
        """
        for f in fields(self):
            setattr(self, f.name, f.default_factory())
        self.update(self.get_defaults())

    def __post_init__(self):
        self.reset()

    def update(self, user_dict: dict):
        field_names = [f.name for f in fields(self)]
        if user_dict is None:
            return
        for k, v in user_dict.items():
            if k not in field_names:
                raise ValueError(
                    f"{k} is not a valid config section. "
                    f"Valid sections: {field_names}"
                )
            if v is None:
                continue
            section = getattr(self, k)
            merge_dict(section, v)


def merge_dict(orig: dict, new: dict) -> dict:
    """
    Update a dict recursively, with values from 'new' being merged into 'orig'.

    Args:
        orig (dict): The object that will receive the update
        new  (dict): The object which is the source of the update

    Example::

            orig = {
                'dict': {'one': 1, 'two': 2},
                'list': [1, 2],
                'string': 's',
            }
            new = {
                'dict': {'one': 'one', 'three': 3},
                'list': [0],
                'string': 'x',
            }
            merge_dict(orig, new) ->
            {
                'dict': {'one': 'one', 'two': 2, 'three': 3}
                'list': [0],
                'string', 'x',
            }

    """
    for k, v in new.items():
        if isinstance(orig, Mapping):
            if isinstance(v, Mapping):
                r = merge_dict(orig.get(k, dict()), v)
                orig[k] = r
            else:
                orig[k] = v
        else:
            orig = {k: v}
    return orig


config = Config()
