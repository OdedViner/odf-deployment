import sys
import os
import yaml
import argparse
import conf


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(THIS_DIR, "default_config.yaml")


def get_defaults():
    with open(DEFAULT_CONFIG_PATH) as file_stream:
        return {
            k: (v if v is not None else {})
            for (k, v) in yaml.safe_load(file_stream).items()
        }


def process_conf_files(arguments):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--webci-conf", action="append", default=[])
    parser.add_argument("--web-version")
    args, unknown = parser.parse_known_args(args=arguments)
    if args.web_version is not None:
        conf.config.ENV["web_version"] = args.web_version
    return args.webci_conf


def load_config(config_files):
    """ """
    for config_file in config_files:
        with open(os.path.abspath(os.path.expanduser(config_file))) as file_stream:
            custom_config_data = yaml.safe_load(file_stream)
            conf.config.update(custom_config_data)


def merge_dicts(list_of_dicts):
    merged_dict = {}
    for dictionary in list_of_dicts:
        merged_dict.update(dictionary)
    return merged_dict


def main(argv=None):
    arguments = argv or sys.argv[1:]
    conf_file_path = process_conf_files(arguments)
    load_config(conf_file_path)
