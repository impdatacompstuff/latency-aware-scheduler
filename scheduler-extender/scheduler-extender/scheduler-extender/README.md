This is an implementation of a scheduler extender. Using the manifests, it will be deployed in the same pod as the kube-scheduler
 
1. Put ./manifests/kube-scheduler-configuration.yaml under /etc/kubernetes/my-scheduler/ on master node
2. kubectl apply -f ../../../manifests/metrics-reader-role.yaml
3. substitute content of /etc/kubernetes/kube-scheduler.yaml with the content of ./manifests/kube-scheduler-with-extender.yaml
4. Wait 20 seconds until kubelet had the chance to check for changes in the kube-scheduler.yaml

