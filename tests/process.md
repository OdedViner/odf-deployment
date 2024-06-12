1.Create new project
oc new-project namespace-test
2.Label namespace "namespace-test"
oc label namespace namespace-test security.openshift.io/scc.podSecurityLabelSync=false pod-security.kubernetes.io/enforce=baseline pod-security.kubernetes.io/warn=baseline --overwrite
3.Create PVC:
```
cat <<EOF | oc create -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-test
  namespace: namespace-test
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 3Gi
  storageClassName: ocs-storagecluster-ceph-rbd
EOF
```
4.Verify pvc in bound state
$ oc get pvc pvc-test -n namespace-test
NAME       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS                  AGE
pvc-test   Bound    pvc-7adc3164-ba98-41b2-bf05-68053b1006a0   3Gi        RWO            ocs-storagecluster-ceph-rbd   19m

5.Create Pod associte to `pvc-test`:
```
cat <<EOF | oc create -f -
apiVersion: v1
kind: Pod
metadata:
  name: pod-test-rbd
  namespace: namespace-test
spec:
  containers:
  - image: quay.io/ocsci/nginx:fio
    name: web-server
    volumeMounts:
    - mountPath: /var/lib/www/html
      name: mypvc
  volumes:
  - name: mypvc
    persistentVolumeClaim:
      claimName: pvc-test
      readOnly: false
EOF
```
6.Verify pod in running state:
$ oc get pod pod-test-rbd -n namespace-test
NAME           READY   STATUS    RESTARTS   AGE
pod-test-rbd   1/1     Running   0          21m

7.Running FIO:
```
oc -n namespace-test rsh pod-test-rbd fio --name=fio-rand-readwrite --filename=/var/lib/www/html/fio-rand-readwrite \
--readwrite=randrw --bs=4K --direct=0 --numjobs=1 --time_based=1 --runtime=30 --size=512M --iodepth=4 --invalidate=0 \
--fsync_on_close=1 --rwmixread=75 --ioengine=libaio --rate=1m --rate_process=poisson --output-format=json
```
8.Delete pod:
```
oc delete pod pod-test-rbd -n namespace-test
```

9.Delete pvc:
```
oc delete pvc pvc-test -n namespace-test
```

10.Delete project
```
oc delete project namespace-test
```