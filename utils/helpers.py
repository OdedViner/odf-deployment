import yaml
import tempfile

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
    # Create a temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".yaml"
    ) as tmp_file:
        # Dump the dictionary to the temporary file
        yaml.dump(data, tmp_file)

    # Return the file path of the temporary file
    return tmp_file.name
