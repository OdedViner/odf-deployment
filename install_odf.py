import time
import yaml


from utils.utils import exec_cmd, TimeoutSampler
from utils.helpers import get_parameters_yaml, verify_status


conf = get_parameters_yaml("conf/configure.yaml")


def label_nodes():
    nodes = conf["worker_nodes"]
    for node in nodes:
        cmd = f"oc label nodes {node} cluster.ocs.openshift.io/openshift-storage='' --overwrite"
        exec_cmd(cmd)


def disable_default_source():
    cmd = """oc patch operatorhub.config.openshift.io/cluster -p='{"spec":{"sources":[{"disabled":true,"name":"redhat-operators"}]}}' --type=merge"""
    exec_cmd(cmd)
    time.sleep(20)
    cmd = f"podman run --entrypoint cat quay.io/rhceph-dev/ocs-registry:latest-stable-4.15 /icsp.yaml"
    icsp = exec_cmd(cmd)
    yaml_data = yaml.safe_load(icsp.stdout.decode("utf-8"))
    file_path = "/tmp/icsp.yaml"
    with open(file_path, "w") as file:
        yaml.dump(yaml_data, file, default_flow_style=False)
    cmd = f"oc apply -f {file_path}"
    exec_cmd(cmd)


def verify_machineconfigpool_status():
    cmd = "oc get MachineConfigPool master --output=json"
    output = exec_cmd(cmd)
    # sample = TimeoutSampler(
    #     timeout=100,
    #     sleep=5,
    #     func=check_element_text,
    #     expected_text=capacity_str,
    # )
    # if not sample.wait_for_func_status(result=True):
    #     raise TimeoutError(f"Disks are not attached after {timeout} seconds")


def create_catalog_source():
    cmd = "oc create -f conf/catalog_source.yaml"
    exec_cmd(cmd)
    cmd = "oc -n openshift-marketplace get CatalogSource redhat-operators  -o yaml"
    sample = TimeoutSampler(
        timeout=100,
        sleep=5,
        func=verify_status,
        cmd=cmd,
        expected_status="lastObservedState: READY",
    )
    if not sample.wait_for_func_status(result=True):
        raise TimeoutError(f"Disks are not attached after 100 seconds")


def create_olm():
    cmd = "oc create -f conf/deploy_with_olm.yaml"
    exec_cmd(cmd)


def create_subscription():
    cmd = "oc create -f conf/subsciption.yaml"
    exec_cmd(cmd)


def verify_csv_status():
    cmd = "oc get csv  -n openshift-storage"
    exec_cmd(cmd)


def apply_storagesystem():
    cmd = "oc apply -f conf/storagesystem_odf.yaml"
    exec_cmd(cmd)


def create_storageclass():
    cmd = "oc create -f conf/storageclass_thin-csi-odf.yaml"
    exec_cmd(cmd)


def create_storagecluster():
    cmd = "oc create -f conf/storagecluster.yaml"
    exec_cmd(cmd)


def run_script():
    # label_nodes()
    # disable_default_source()
    # verify_machineconfigpool_status()
    # create_catalog_source()
    # create_olm()
    create_subscription()
    # verify_csv_status()
    # apply_storagesystem()
    # create_storageclass()
    # create_storagecluster()


if __name__ == "__main__":
    run_script()
