package main

import (
	"github.com/julienschmidt/httprouter"
	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	extender "k8s.io/kube-scheduler/extender/v1"
	"log"
	"math/rand"
	"net/http"
	"time"
)

func init() {
	rand.Seed(time.Now().UTC().UnixNano())
}

func main() {
	//log.Print("Welcome to the extender!")

	/*
	 *  actual routing functionality
	 */
	router := httprouter.New()
	router.GET("/", Index)
	router.POST("/filter", Filter)
	//router.POST("/prioritize", Prioritize)

	log.Fatal(http.ListenAndServe(":8888", router))

	//requestThings("master.k8s")

	/*
	 *  The following code serves testing purposes
	 */
	//node := createTestNode()
	//pod := createTestPod()
	//
	//latencies := getRequests(&pod, "example.com/udp-mbpns")
	//min := findMax(latencies)
	//fmt.Print(min)

	//nodeList := createTestNodeList([]v1.Node{node})
	//fmt.Printf("%#v", requestLatencyMetrics(node))
	//fits, str, err := podFitsOnNode(&pod, node)
	//fmt.Printf("%#v %#v %#v", fits, str, err)
	//result := filter(createExtenderArgs(pod, nodeList))
	//fmt.Sprintf("%#v", result)
}

func createExtenderArgs(pod v1.Pod, nodeList v1.NodeList) extender.ExtenderArgs {
	extenderArgs := extender.ExtenderArgs{
		Pod:       &pod,
		Nodes:     &nodeList,
		NodeNames: nil,
	}
	return extenderArgs
}

func createTestNodeList(nodes []v1.Node) v1.NodeList {
	nodeList := v1.NodeList{
		TypeMeta: metav1.TypeMeta{
			Kind:       "",
			APIVersion: "",
		},
		ListMeta: metav1.ListMeta{
			SelfLink:           "",
			ResourceVersion:    "",
			Continue:           "",
			RemainingItemCount: nil,
		},
		Items: nodes,
	}
	return nodeList
}

func createTestPod() v1.Pod {
	resourceListMap0 := make(map[v1.ResourceName]resource.Quantity)
	resourceListMap0[v1.ResourceMemory], _ = resource.ParseQuantity("500m")
	resourceListMap0[v1.ResourceCPU], _ = resource.ParseQuantity("500m")
	resourceListMap0["example.com/latency-nanos"], _ = resource.ParseQuantity("500")
	resourceListMap0["example.com/udp-mbpns"], _ = resource.ParseQuantity("500")

	resourceListMap1 := make(map[v1.ResourceName]resource.Quantity)
	resourceListMap1[v1.ResourceMemory], _ = resource.ParseQuantity("500m")
	resourceListMap1[v1.ResourceCPU], _ = resource.ParseQuantity("500m")
	resourceListMap1["example.com/latency-nanos"], _ = resource.ParseQuantity("400")
	resourceListMap1["example.com/udp-mbpns"], _ = resource.ParseQuantity("400")

	resourceListMap2 := make(map[v1.ResourceName]resource.Quantity)
	resourceListMap2[v1.ResourceMemory], _ = resource.ParseQuantity("500m")
	resourceListMap2[v1.ResourceCPU], _ = resource.ParseQuantity("500m")
	resourceListMap2["example.com/latency-nanos"], _ = resource.ParseQuantity("200")
	resourceListMap2["example.com/udp-mbpns"], _ = resource.ParseQuantity("200")

	container0 := v1.Container{
		Name:       "container0",
		Image:      "",
		Command:    nil,
		Args:       nil,
		WorkingDir: "",
		Ports:      nil,
		EnvFrom:    nil,
		Env:        nil,
		Resources: v1.ResourceRequirements{
			Limits:   nil,
			Requests: resourceListMap0,
		},
		VolumeMounts:             nil,
		VolumeDevices:            nil,
		LivenessProbe:            nil,
		ReadinessProbe:           nil,
		StartupProbe:             nil,
		Lifecycle:                nil,
		TerminationMessagePath:   "",
		TerminationMessagePolicy: v1.TerminationMessageFallbackToLogsOnError,
		ImagePullPolicy:          v1.PullAlways,
		SecurityContext:          nil,
		Stdin:                    true,
		StdinOnce:                true,
		TTY:                      true,
	}
	container1 := v1.Container{
		Name:       "container1",
		Image:      "",
		Command:    nil,
		Args:       nil,
		WorkingDir: "",
		Ports:      nil,
		EnvFrom:    nil,
		Env:        nil,
		Resources: v1.ResourceRequirements{
			Limits:   nil,
			Requests: resourceListMap1,
		},
		VolumeMounts:             nil,
		VolumeDevices:            nil,
		LivenessProbe:            nil,
		ReadinessProbe:           nil,
		StartupProbe:             nil,
		Lifecycle:                nil,
		TerminationMessagePath:   "",
		TerminationMessagePolicy: v1.TerminationMessageFallbackToLogsOnError,
		ImagePullPolicy:          v1.PullAlways,
		SecurityContext:          nil,
		Stdin:                    true,
		StdinOnce:                true,
		TTY:                      true,
	}

	container2 := v1.Container{
		Name:       "container1",
		Image:      "",
		Command:    nil,
		Args:       nil,
		WorkingDir: "",
		Ports:      nil,
		EnvFrom:    nil,
		Env:        nil,
		Resources: v1.ResourceRequirements{
			Limits:   nil,
			Requests: resourceListMap2,
		},
		VolumeMounts:             nil,
		VolumeDevices:            nil,
		LivenessProbe:            nil,
		ReadinessProbe:           nil,
		StartupProbe:             nil,
		Lifecycle:                nil,
		TerminationMessagePath:   "",
		TerminationMessagePolicy: v1.TerminationMessageFallbackToLogsOnError,
		ImagePullPolicy:          v1.PullAlways,
		SecurityContext:          nil,
		Stdin:                    true,
		StdinOnce:                true,
		TTY:                      true,
	}

	containerList := []v1.Container{container0, container1, container2}

	pod := v1.Pod{
		TypeMeta: metav1.TypeMeta{
			Kind:       "",
			APIVersion: "",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:                       "poddy",
			GenerateName:               "",
			Namespace:                  "",
			SelfLink:                   "",
			UID:                        "",
			ResourceVersion:            "",
			Generation:                 0,
			CreationTimestamp:          metav1.Time{},
			DeletionTimestamp:          nil,
			DeletionGracePeriodSeconds: nil,
			Labels:                     nil,
			Annotations:                nil,
			OwnerReferences:            nil,
			Finalizers:                 nil,
			ManagedFields:              nil,
		},
		Spec: v1.PodSpec{
			Volumes:                       nil,
			InitContainers:                nil,
			Containers:                    containerList,
			EphemeralContainers:           nil,
			RestartPolicy:                 "",
			TerminationGracePeriodSeconds: nil,
			ActiveDeadlineSeconds:         nil,
			DNSPolicy:                     "",
			NodeSelector:                  nil,
			ServiceAccountName:            "",
			DeprecatedServiceAccount:      "",
			AutomountServiceAccountToken:  nil,
			NodeName:                      "",
			HostNetwork:                   false,
			HostPID:                       false,
			HostIPC:                       false,
			ShareProcessNamespace:         nil,
			SecurityContext:               nil,
			ImagePullSecrets:              nil,
			Hostname:                      "",
			Subdomain:                     "",
			Affinity:                      nil,
			SchedulerName:                 "",
			Tolerations:                   nil,
			HostAliases:                   nil,
			PriorityClassName:             "",
			Priority:                      nil,
			DNSConfig:                     nil,
			ReadinessGates:                nil,
			RuntimeClassName:              nil,
			EnableServiceLinks:            nil,
			PreemptionPolicy:              nil,
			Overhead:                      nil,
			TopologySpreadConstraints:     nil,
			SetHostnameAsFQDN:             nil,
			OS:                            nil,
			HostUsers:                     nil,
		},
		Status: v1.PodStatus{
			Phase:                      "",
			Conditions:                 nil,
			Message:                    "",
			Reason:                     "",
			NominatedNodeName:          "",
			HostIP:                     "",
			PodIP:                      "",
			PodIPs:                     nil,
			StartTime:                  nil,
			InitContainerStatuses:      nil,
			ContainerStatuses:          nil,
			QOSClass:                   "",
			EphemeralContainerStatuses: nil,
		},
	}
	return pod
}

func createTestNode() v1.Node {
	node := v1.Node{
		TypeMeta: metav1.TypeMeta{
			Kind:       "",
			APIVersion: "",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:                       "myNode",
			GenerateName:               "",
			Namespace:                  "my-node-namespace",
			SelfLink:                   "",
			UID:                        "",
			ResourceVersion:            "",
			Generation:                 0,
			CreationTimestamp:          metav1.Time{},
			DeletionTimestamp:          nil,
			DeletionGracePeriodSeconds: nil,
			Labels:                     nil,
			Annotations:                nil,
			OwnerReferences:            nil,
			Finalizers:                 nil,
			ManagedFields:              nil,
		},
		Spec: v1.NodeSpec{
			PodCIDR:            "",
			PodCIDRs:           nil,
			ProviderID:         "",
			Unschedulable:      false,
			Taints:             nil,
			ConfigSource:       nil,
			DoNotUseExternalID: "",
		},
		Status: v1.NodeStatus{
			Capacity:        nil,
			Allocatable:     nil,
			Phase:           "",
			Conditions:      nil,
			Addresses:       nil,
			DaemonEndpoints: v1.NodeDaemonEndpoints{},
			NodeInfo:        v1.NodeSystemInfo{},
			Images:          nil,
			VolumesInUse:    nil,
			VolumesAttached: nil,
			Config:          nil,
		},
	}
	return node
}
