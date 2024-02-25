import yaml
import tempfile
import re
import semantic_version

from utils.utils import exec_cmd
from utils.logger_setup import setup_logger


log = setup_logger()


def get_parameters_yaml(file_path):
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    return data


def verify_status(cmd, expected_status):
    output = exec_cmd(cmd)
    string_output = output.stdout.decode("utf-8")
    return expected_status in string_output


def convert_yaml_to_dict(file_path):
    with open(file_path, "r") as file:
        yaml_data = yaml.safe_load(file)
    return yaml_data


def save_dict_to_yaml(data):
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".yaml"
    ) as tmp_file:
        yaml.dump(data, tmp_file)

    return tmp_file.name


def check_count_occurrences(cmd, substring, mount):
    output = exec_cmd(cmd)
    string_output = output.stdout.decode("utf-8")
    occurrences = string_output.count(substring)
    return occurrences >= mount


def get_version(version_string):
    pattern = re.compile(r'\d+\.\d+|\d+')
    matches = pattern.findall(version_string)
    return semantic_version.Version.coerce(matches[0])