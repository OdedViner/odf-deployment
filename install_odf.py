import time


from utils.utils import exec_cmd


def label_nodes():
    cmd = "oc label nodes compute-0 compute-1 compute-2 cluster.ocs.openshift.io/openshift-storage='' --overwrite"
    exec_cmd(cmd)


def disable_default_source():
    cmd = """
    oc patch operatorhub.config.openshift.io/cluster -p=
    '{"spec":{"sources":[{"disabled":true,"name":"redhat-operators"}]}}' --type=merge
    """
    exec_cmd(cmd)
    time.sleep(20)
    cmd = (
        "podman run --entrypoint cat quay.io/rhceph-dev/ocs-registry:latest-stable-4.15  "
        "/icsp.yaml | oc apply -f -"
    )
    exec_cmd(cmd)


def verify_machineconfigpool_status():
    cmd = "oc get MachineConfigPool master"
    exec_cmd(cmd)


def create_catalog_source():
    cmd = "oc create -f conf/CatalogSource.yaml"
    exec_cmd(cmd)
    cmd = "oc -n openshift-marketplace get CatalogSource redhat-operators  -o yaml | grep -i lastObservedState:"
    exec_cmd(cmd)


def create_olm():
    cmd = "oc create -f conf/deploy-with-olm.yaml"
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
    label_nodes()
    disable_default_source()
    verify_machineconfigpool_status()
    create_catalog_source()
    create_olm()
    create_subscription()
    verify_csv_status()
    apply_storagesystem()
    create_storageclass()
    create_storagecluster()


if __name__ == "__main__":
    run_script()
