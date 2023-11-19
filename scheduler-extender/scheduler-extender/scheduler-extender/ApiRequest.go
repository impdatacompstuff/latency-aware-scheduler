package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"k8s.io/apimachinery/pkg/api/resource"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/metrics/pkg/apis/custom_metrics"
	"log"
	"os"
	"time"
)

const kubeconfigPath = "/etc/kubernetes/scheduler.conf"

var dynamicClient = createDynamicClient()

func requestLatencyMetrics(nodeName string) (float64, error) {
	//reader := readMetricValueList()
	//metricValueList := decodeMetricValueList(reader)
	//defer reader.Close()

	metricValueList, err := requestNodeLatency(nodeName)
	if err != nil {
		return 0, err
	}
	//TODO: handle metricValueList == nil
	quantity := extractQuantity(metricValueList)
	return quantity.AsApproximateFloat64(), err
}

func requestTCPBandwidthMetrics(nodeName string) (int64, error) {
	metricValueList, err := requestNodeTCPBandwidth(nodeName)
	if err != nil {
		return 0, err
	}
	//TODO: handle metricValueList == nil
	quantity := extractQuantity(metricValueList)
	return quantity.MilliValue(), err
}

func requestUDPBandwidthMetrics(nodeName string) (int64, error) {
	metricValueList, err := requestNodeUDPBandwidth(nodeName)
	if err != nil {
		return 0, err
	}
	//TODO: handle metricValueList == nil
	quantity := extractQuantity(metricValueList)
	return quantity.MilliValue(), err
}

func requestJitterMetrics(nodeName string) (int64, error) {
	metricValueList, err := requestNodeJitter(nodeName)
	if err != nil {
		return 0, err
	}
	//TODO: handle metricValueList == nil
	quantity := extractQuantity(metricValueList)
	return quantity.MilliValue(), err
}

func requestNodeLatency(nodeName string) (*custom_metrics.MetricValueList, error) {
	gvrNodeMetric := schema.GroupVersionResource{
		Group:    "custom.metrics.k8s.io",
		Version:  "v1beta1",
		Resource: fmt.Sprintf("nodes/%s/example.com~1latency-nanos", nodeName),
	}

	//log.Printf("Requesting node latency-millis metrics ...")
	////TODO: validate for 200 status
	////TODO: return something valid on error
	nodeMetrics, err := sendListRequest(gvrNodeMetric, "")
	if err != nil {
		return nil, err
	}
	nodeLatencyMillis, _ := convertToMetricValueList(nodeMetrics)
	return nodeLatencyMillis, err
}

func requestNodeTCPBandwidth(nodeName string) (*custom_metrics.MetricValueList, error) {
	gvrNodeMetric := schema.GroupVersionResource{
		Group:    "custom.metrics.k8s.io",
		Version:  "v1beta1",
		Resource: fmt.Sprintf("nodes/%s/example.com~1tcp-mbpns", nodeName),
	}

	//log.Printf("Requesting node tcp-mbpns metrics ...")
	////TODO: validate for 200 status
	////TODO: return something valid on error
	nodeMetrics, err := sendListRequest(gvrNodeMetric, "")
	if err != nil {
		return nil, err
	}
	tcpBandwidth, _ := convertToMetricValueList(nodeMetrics)
	return tcpBandwidth, err
}

func requestNodeUDPBandwidth(nodeName string) (*custom_metrics.MetricValueList, error) {
	gvrNodeMetric := schema.GroupVersionResource{
		Group:    "custom.metrics.k8s.io",
		Version:  "v1beta1",
		Resource: fmt.Sprintf("nodes/%s/example.com~1udp-mbpns", nodeName),
	}

	//log.Printf("Requesting node udp-mbpns metrics ...")
	////TODO: validate for 200 status
	////TODO: return something valid on error
	nodeMetrics, err := sendListRequest(gvrNodeMetric, "")
	if err != nil {
		return nil, err
	}
	udpBandwidth, _ := convertToMetricValueList(nodeMetrics)
	return udpBandwidth, err
}

func requestNodeJitter(nodeName string) (*custom_metrics.MetricValueList, error) {
	gvrNodeMetric := schema.GroupVersionResource{
		Group:    "custom.metrics.k8s.io",
		Version:  "v1beta1",
		Resource: fmt.Sprintf("nodes/%s/example.com~1jitter", nodeName),
	}

	//log.Printf("Requesting node jitter metrics ...")
	////TODO: validate for 200 status
	////TODO: return something valid on error
	nodeMetrics, err := sendListRequest(gvrNodeMetric, "")
	if err != nil {
		return nil, err
	}
	jitter, _ := convertToMetricValueList(nodeMetrics)
	return jitter, err
}

/* For running locally only */
func readMetricValueList() *os.File {
	//Open test json - for prod to be replaced by call to the metrics server
	jsonFile, err := os.Open("MetricValueListTestData.json")
	if err != nil {
		fmt.Println(err.Error())
	}
	return jsonFile
}

func requestThings(nodeName string) {
	//log.Printf("Requesting Pod names ...")
	//userHomeDir, err := os.UserHomeDir()
	//if err != nil {
	//	fmt.Printf("error getting user home dir: %v\n", err)
	//	//os.Exit(1)
	//}

	gvrPods := createGvr("", "v1", "pods")

	sendGetRequest(gvrPods, "susi", "default")

	//pods, err := dynamicClient.Resource(gvrPods).Namespace("kube-system").List(context.Background(), metav1.ListOptions{})
	//if err != nil {
	//	log.Printf("error getting pods: %v\n", err)
	//	//os.Exit(1)
	//}
	//
	//for _, pod := range pods.Items {
	//	log.Printf(
	//		"Name: %s\n",
	//		pod.Object["metadata"].(map[string]interface{})["name"],
	//	)
	//}

	//gvrPodMetric := createGvr("custom.metrics.k8s.io", "v1beta1", "pods/susi/packets-per-second")
	//metricsUnstructuredList := sendListRequest(gvrPodMetric, "default")

	//metricValueList, err := convertToMetricValueList(metricsUnstructuredList)

	//for _, item := range metricValueList.Items {
	//	value := item.Value.MilliValue()
	//	//log.Printf("extracted metric value for pod %s: %d", item.DescribedObject.Name, value)
	//}

	//log.Printf("Requesting node metrics ...")
	//gvrNodeMetric := createGvr("custom.metrics.k8s.io", "v1beta1", fmt.Sprintf("nodes/%s/latency-millis", nodeName))

	//nodeMetrics := sendListRequest(gvrNodeMetric, "")

	//nodeMetricValueList, err := convertToMetricValueList(nodeMetrics)
	//if err != nil {
	//	log.Printf("error converting unstructured to metricvaluelist: %v\n", err)
	//}

	//log.Printf("selfLink: %s", nodeMetricValueList.ListMeta.GetSelfLink())

	//for _, item := range nodeMetricValueList.Items {
	//	value := item.Value.MilliValue()
	//	//log.Printf("extracted metric value for node %s: %d", item.DescribedObject.Name, value)
	//}
}

func sendListRequest(gvr schema.GroupVersionResource, namespace string) (*unstructured.UnstructuredList, error) {
	if namespace == "" {
		unstructuredList, err := dynamicClient.Resource(gvr).List(context.Background(), v1.ListOptions{})
		//if err != nil {
		//	log.Printf("error listing %s: %v\n", gvr.Resource, err)
		//	//os.Exit(1)
		//	time.Sleep(35 * time.Millisecond)
		//	unstructuredList, err = dynamicClient.Resource(gvr).List(context.Background(), v1.ListOptions{})
		//}
		//log.Printf("%s", unstructuredList.Object["metadata"].(map[string]interface{})["selfLink"])
		return unstructuredList, err
	} else {
		unstructuredList, err := dynamicClient.Resource(gvr).Namespace(namespace).List(context.Background(), v1.ListOptions{})
		if err != nil {
			log.Printf("error listing %s: %v\n", gvr.Resource, err)
			//os.Exit(1)
			time.Sleep(500 * time.Millisecond)
			unstructuredList, err = dynamicClient.Resource(gvr).Namespace(namespace).List(context.Background(), v1.ListOptions{})
		}
		//log.Printf("%s", unstructuredList.Object["metadata"].(map[string]interface{})["selfLink"])
		return unstructuredList, err
	}
}

func sendGetRequest(gvr schema.GroupVersionResource, name string, namespace string) unstructured.Unstructured {
	if namespace == "" {
		unstructrd, err := dynamicClient.Resource(gvr).Get(context.Background(), name, v1.GetOptions{})
		if err != nil {
			log.Printf("error getting %s from %s: %v\n", gvr.Resource, name, err)
			//os.Exit(1)
		}
		//log.Printf("%s", unstructrd.Object["metadata"].(map[string]interface{})["name"])
		return *unstructrd
	} else {
		unstructrd, err := dynamicClient.Resource(gvr).Namespace(namespace).Get(context.Background(), name, v1.GetOptions{})
		if err != nil {
			log.Printf("error getting %s from %s: %v\n", gvr.Resource, name, err)
			//os.Exit(1)
		}
		//log.Printf("%s", unstructrd.Object["metadata"].(map[string]interface{})["name"])
		return *unstructrd
	}
}

func convertToMetricValueList(metrics *unstructured.UnstructuredList) (*custom_metrics.MetricValueList, error) {
	metricValueList := &custom_metrics.MetricValueList{}
	unstructrd := metrics.UnstructuredContent()
	err := runtime.DefaultUnstructuredConverter.FromUnstructured(unstructrd, metricValueList)
	if err != nil {
		log.Printf("error converting unstructrd to metricvaluelist: %v\n", err)
	}
	return metricValueList, err
}

/* For running locally only */
func decodeMetricValueList(reader io.Reader) custom_metrics.MetricValueList {
	var metricValueList custom_metrics.MetricValueList

	var buf bytes.Buffer
	body := io.TeeReader(reader, &buf)
	//log.Printf("Received MetricValueList data to decode: %#v", body)
	if err := json.NewDecoder(body).Decode(&metricValueList); err != nil {
		println(err.Error())

	} else {
		//log.Printf("Decoded data: %#v", metricValueList)
	}

	return metricValueList
}

func extractQuantity(metricValueList *custom_metrics.MetricValueList) resource.Quantity {
	//TODO check for various
	metricValue := metricValueList.Items[0].Value
	//log.Printf("Extracted metric value is %#v", metricValue)
	return metricValue
}

func createGvr(group string, version string, resource string) schema.GroupVersionResource {
	gvrPods := schema.GroupVersionResource{
		Group:    group,
		Version:  version,
		Resource: resource,
	}
	return gvrPods
}

func createDynamicClient() dynamic.Interface {
	config, _ := createConfig()
	return newFor(config)
}

func newFor(config *rest.Config) dynamic.Interface {
	dynamicClient, err := dynamic.NewForConfig(config)
	if err != nil {
		log.Printf("error creating dynamic client: %v\n", err)
		return nil
	}
	return dynamicClient
}

func createConfig() (*rest.Config, error) {
	kubeConfigPath := kubeconfigPath
	//fmt.Printf("Using kubeconfig: %s\n", kubeConfigPath)

	config, err := clientcmd.BuildConfigFromFlags("", kubeConfigPath)
	if err != nil {
		fmt.Printf("error getting Kubernetes config: %v\n", err)
		//os.Exit(1)
	}
	return config, err
}
