import time
import json


from utils.utils import exec_cmd, TimeoutSampler
from utils.helpers import verify_status
from utils.logger_setup import setup_logger

log = setup_logger()

def create_project():
    cmd = "oc new-project namespace-test"
    exec_cmd(cmd)
    time.sleep(2)
    cmd = "oc label namespace namespace-test security.openshift.io/scc.podSecurityLabelSync=false pod-security.kubernetes.io/enforce=baseline pod-security.kubernetes.io/warn=baseline --overwrite"
    exec_cmd(cmd)
    time.sleep(2)

def label_name_space():
    cmd = "oc label namespace namespace-test security.openshift.io/scc.podSecurityLabelSync=false " \
          "pod-security.kubernetes.io/enforce=baseline pod-security.kubernetes.io"
    exec_cmd(cmd)
    time.sleep(2)

def create_pvc(sc_name):
    if sc_name == "ceph-fs":
        cmd = "oc apply -f conf/pvc_ceph_fs.yaml"
    else:
        cmd = "oc apply -f conf/pvc_ceph_rbd.yaml"
    exec_cmd(cmd)
    time.sleep(2)

def verify_pvc_on_bound_state():
    cmd = "oc get pvc pvc-test -n namespace-test"
    sample = TimeoutSampler(
        timeout=60,
        sleep=5,
        func=verify_status,
        cmd=cmd,
        expected_status="Bound",
    )
    if not sample.wait_for_func_status(result=True):
        raise TimeoutError(f"The pvc is not on Bound state after 60 Sec")

def create_pod_assosiate_pvc():
    cmd = "oc apply -f conf/pod.yaml"
    exec_cmd(cmd)
    time.sleep(2)

def verify_pod_in_running_state():
    cmd = " oc get pod pod-test -n namespace-test"
    sample = TimeoutSampler(
        timeout=100,
        sleep=10,
        func=verify_status,
        cmd=cmd,
        expected_status="Running",
    )
    if not sample.wait_for_func_status(result=True):
        raise TimeoutError(f"The pod is not on Running state after 100 Sec")


def running_fio():
    cmd = "oc -n namespace-test rsh pod-test fio --name=fio-rand-readwrite \
    --filename=/var/lib/www/html/fio-rand-readwrite \
    --readwrite=randrw --bs=4K --direct=0 --numjobs=1 --time_based=1 --runtime=5 \
    --size=1024M --iodepth=4 --invalidate=0 \
    --fsync_on_close=1 --rwmixread=75 --ioengine=libaio --rate=1m --rate_process=poisson --output-format=json"
    exec_cmd(cmd)
    # fio_reslts_process = exec_cmd(cmd)
    #
    # python_dict = json.loads(fio_reslts_process.stdout)
    # log.info(f"write_ios={python_dict['disk_util'][0]['write_ios']}")
    # log.info(f"write_ios={python_dict['disk_util'][0]['read_ios']}")
def delete_pod():
    cmd = "oc delete pod pod-test -n namespace-test"
    exec_cmd(cmd)
    time.sleep(2)

def delete_pvc():
    cmd = "oc delete pvc pvc-test -n namespace-test"
    exec_cmd(cmd)
    time.sleep(2)

def delete_project():
    cmd = "oc delete project namespace-test"
    exec_cmd(cmd)
    time.sleep(2)


if __name__ == "__main__":
    # delete_pod()
    # delete_pvc()
    # delete_project()
    # delete_project()
    # try:
    #     delete_pod()
    #     delete_pvc()
    #     delete_project()
    # except Exception as e:
    #     print(f"Error during cleanup: {e}")
    # delete_pod()
    # delete_pvc()
    # # delete_project()
    try:
        sc_name = "ceph-fs1"
        # create_project()
        # label_name_space()
        create_pvc(sc_name)
        verify_pvc_on_bound_state()
        create_pod_assosiate_pvc()
        verify_pod_in_running_state()
        # running_fio()
        # delete_pod()
        # delete_pvc()
        # delete_project()
    except Exception as e:
        print(f"Error during cleanup: {e}")
        # delete_pod()
        # delete_pvc()
        # delete_project()
       


