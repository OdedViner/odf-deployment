import time
import yaml
import semantic_version


from utils.utils import exec_cmd, TimeoutSampler
from utils.helpers import (
    get_parameters_yaml,
    verify_status,
    convert_yaml_to_dict,
    save_dict_to_yaml,
    check_count_occurrences,
    get_version,
)


conf = get_parameters_yaml("conf/configure.yaml")


def get_worker_nodes():
    cmd = "oc get nodes -l node-role.kubernetes.io/worker -o jsonpath='{.items[*].metadata.name}'"
    result = exec_cmd(cmd)
    nodes = result.stdout.decode("utf-8").strip("'").split()
    print(nodes)
    return nodes


def label_nodes():
    nodes = get_worker_nodes()
    for node in nodes:
        cmd = f"oc label nodes {node} cluster.ocs.openshift.io/openshift-storage='' --overwrite"
        exec_cmd(cmd)


def disable_default_source():
    cmd = """oc patch operatorhub.config.openshift.io/cluster -p='{"spec":{"sources":[{"disabled":true,"name":"redhat-operators"}]}}' --type=merge"""
    exec_cmd(cmd)
    time.sleep(20)
    cmd = f"podman run --entrypoint cat {conf['odf_version']} /icsp.yaml"
    icsp = exec_cmd(cmd)
    yaml_data = yaml.safe_load(icsp.stdout.decode("utf-8"))
    file_path = "/tmp/icsp.yaml"
    with open(file_path, "w") as file:
        yaml.dump(yaml_data, file, default_flow_style=False)
    cmd = f"oc apply -f {file_path}"
    exec_cmd(cmd)


def verify_machineconfigpool_status():
    cmd = "oc get MachineConfigPool worker"
    worker_count = len(conf.get("worker_nodes") or get_worker_nodes())
    sample = TimeoutSampler(
        timeout=200,
        sleep=5,
        func=check_count_occurrences,
        cmd=cmd,
        substring=f'{worker_count}  ',
        mount=worker_count,
    )
    if not sample.wait_for_func_status(result=True):
        raise TimeoutError("MachineConfigPool is not ready after 200 seconds")


def create_catalog_source():
    catalog_dict = convert_yaml_to_dict("conf/catalog_source.yaml")
    catalog_dict["spec"]["image"] = conf["odf_version"]
    yaml_path = save_dict_to_yaml(catalog_dict)
    cmd = f"oc apply -f {yaml_path}"
    exec_cmd(cmd)
    cmd = "oc -n openshift-marketplace get CatalogSource redhat-operators  -o yaml"
    sample = TimeoutSampler(
        timeout=150,
        sleep=5,
        func=verify_status,
        cmd=cmd,
        expected_status="lastObservedState: READY",
    )
    if not sample.wait_for_func_status(result=True):
        raise TimeoutError("CatalogSource is not ready after 150 seconds")
    cmd = "oc apply -f conf/operator_group.yaml"
    exec_cmd(cmd)


def create_subscription():
    subscription_dict = convert_yaml_to_dict("conf/subsciption.yaml")
    subscription_dict["spec"]["channel"] = conf["odf_channel"]
    yaml_path = save_dict_to_yaml(subscription_dict)
    cmd = f"oc apply -f {yaml_path}"
    exec_cmd(cmd)


def verify_csv_status():
    cmd = "oc get csv -n openshift-storage"
    sample = TimeoutSampler(
        timeout=600,
        sleep=5,
        func=check_count_occurrences,
        cmd=cmd,
        substring="Succeeded",
        mount=13,
    )
    if not sample.wait_for_func_status(result=True):
        raise TimeoutError("CSV did not succeed after 600 seconds")


def apply_networkpolicy():
    rook_base = "https://raw.githubusercontent.com/red-hat-storage/rook/master/build/csv/ceph"
    odf_base = (
        "https://raw.githubusercontent.com/OdedViner/odf-operator"
        "/7791882ec1dcc2b90acc02d51f45ba1a0c9a8f00/config/networkpolicy"
    )

    urls = [
        f"{rook_base}/networkpolicy.yaml",
        f"{odf_base}/ceph-csi-operator/ceph-csi-operator-controller-manager-networkpolicy.yaml",
        f"{odf_base}/ceph-csi-operator/csi-addons-controller-manager-networkpolicy.yaml",
        f"{odf_base}/ceph-csi/cephfs-ctrlplugin-networkpolicy.yaml",
        f"{odf_base}/ceph-csi/cephfs-nodeplugin-csi-addons-networkpolicy.yaml",
        f"{odf_base}/ceph-csi/rbd-ctrlplugin-networkpolicy.yaml",
        f"{odf_base}/ceph-csi/rbd-nodeplugin-csi-addons-networkpolicy.yaml",
        f"{odf_base}/noobaa/cnpg-controller-manager-networkpolicy.yaml",
        f"{odf_base}/noobaa/noobaa-core-networkpolicy.yaml",
        f"{odf_base}/noobaa/noobaa-db-pg-cluster-networkpolicy.yaml",
        f"{odf_base}/noobaa/noobaa-endpoint-networkpolicy.yaml",
        f"{odf_base}/noobaa/noobaa-operator-networkpolicy.yaml",
        f"{odf_base}/ocs-client-operator/ocs-client-operator-console-networkpolicy.yaml",
        f"{odf_base}/ocs-client-operator/ocs-client-operator-controller-manager-networkpolicy.yaml",
        f"{odf_base}/ocs-operator/ocs-metrics-exporter-networkpolicy.yaml",
        f"{odf_base}/ocs-operator/ocs-operator-networkpolicy.yaml",
        f"{odf_base}/ocs-operator/ocs-provider-server-networkpolicy.yaml",
        f"{odf_base}/odf-operator/odf-blackbox-exporter-networkpolicy.yaml",
        f"{odf_base}/odf-operator/odf-console-networkpolicy.yaml",
        f"{odf_base}/odf-operator/odf-external-snapshotter-operator-networkpolicy.yaml",
        f"{odf_base}/odf-operator/odf-operator-controller-manager-networkpolicy.yaml",
        f"{odf_base}/odf-operator/ux-backend-server-networkpolicy.yaml",
    ]

    for url in urls:
        cmd = f"oc apply -f {url}"
        exec_cmd(cmd)


def create_storageclass():
    if conf["platform"] == "vsphere":
        path = "conf/storageclass_thin-csi-odf.yaml"
        cmd = f"oc apply -f {path}"
        exec_cmd(cmd)
        time.sleep(2)
    elif conf["platform"] == "ibm":
        pass


def create_storagecluster():
    platform = conf["platform"]
    storage_class_map = {
        "ibm": "ibmc-vpc-block-10iops-tier",
        "vsphere": "thin-csi-odf",
    }
    storagecluster_dict = convert_yaml_to_dict("conf/storagecluster.yaml")
    storage_class = storage_class_map.get(platform)
    if storage_class:
        storagecluster_dict["spec"]["storageDeviceSets"][0]["dataPVCTemplate"][
            "spec"
        ]["storageClassName"] = storage_class
    yaml_path = save_dict_to_yaml(storagecluster_dict)
    cmd = f"oc apply -f {yaml_path}"
    exec_cmd(cmd)



def crerte_tool_pod():
    version = get_version(conf["odf_channel"])
    if version >= semantic_version.Version.coerce("4.15"):
        cmd = """oc patch storagecluster ocs-storagecluster -n openshift-storage --type json --patch \
        '[{ "op": "replace", "path": "/spec/enableCephTools", "value": true }]'"""
    else:
        cmd = """oc patch ocsinitialization ocsinit -n openshift-storage --type json --patch \
        '[{ "op": "replace", "path": "/spec/enableCephTools", "value": true }]'"""
    exec_cmd(cmd)


def run_script():
    label_nodes()
    disable_default_source()
    verify_machineconfigpool_status()
    create_catalog_source()
    # create_operator_group()
    create_subscription()
    verify_csv_status()
    apply_networkpolicy()
    create_storageclass()
    create_storagecluster()
    crerte_tool_pod()


if __name__ == "__main__":
    run_script()
