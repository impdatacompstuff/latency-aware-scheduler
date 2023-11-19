package main

import (
	"fmt"
	v1 "k8s.io/api/core/v1"
	extender "k8s.io/kube-scheduler/extender/v1"
	"log"
	"sort"
	"strings"
)

const (
	LatencyPred      = "Latency Tolerance"
	TCPBandwidthPred = "Bandwidth measured by TCP"
	UDPBandwidthPred = "Bandwidth measured by UDP"
	JitterPred       = "Jitter"
)

var predicates = map[string]FitPredicate{
	LatencyPred:      LatencyPredicate,
	TCPBandwidthPred: TCPBandwidthPredicate,
	UDPBandwidthPred: UDPBandwidthPredicate,
	JitterPred:       JitterPredicate,
}

type FitPredicate func(pod *v1.Pod, node v1.Node) (bool, []string, error)

var predicatesSorted = []string{
	LatencyPred,
	TCPBandwidthPred,
	UDPBandwidthPred,
	JitterPred,
}

// filter filters nodes according to predicates defined in this extender
// it's webhooked to pkg/scheduler/core/generic_scheduler.go#findNodesThatFitPod()

func filter(args extender.ExtenderArgs) *extender.ExtenderFilterResult {
	var filteredNodes []v1.Node
	failedNodes := make(extender.FailedNodesMap)
	pod := args.Pod

	for _, node := range args.Nodes.Items {
		fits, failReasons, _ := podFitsOnNode(pod, node)
		if fits {
			filteredNodes = append(filteredNodes, node)
		} else {
			failedNodes[node.Name] = strings.Join(failReasons, ",")
		}
	}

	result := extender.ExtenderFilterResult{
		Nodes: &v1.NodeList{
			Items: filteredNodes,
		},
		FailedNodes: failedNodes,
		Error:       "",
	}

	return &result
}

func podFitsOnNode(pod *v1.Pod, node v1.Node) (bool, []string, error) {
	fits := true
	var failReasons []string
	for _, predicateKey := range predicatesSorted {
		fit, failures, err := predicates[predicateKey](pod, node)
		if err != nil {
			log.Printf("error: %s", err.Error())
			return false, nil, err
		}
		fits = fits && fit
		failReasons = append(failReasons, failures...)
	}
	return fits, failReasons, nil
}

func LatencyPredicate(pod *v1.Pod, node v1.Node) (bool, []string, error) {
	//log.Printf("in LatencyPredicate")
	latencies := getRequests(pod, "example.com/latency-nanos")
	if len(latencies) == 0 {
		return true, []string{}, nil
	}

	minTolerableLatencyAsMilli := findMin(latencies)
	//minTolerableLatencyAsNano := toNano(minTolerableLatencyAsMilli)

	//log.Printf("Pod tolerates up to %f latency-nanos", minTolerableLatencyAsNano)
	nodeLatencyMillis, err := requestLatencyMetrics(node.GetName())
	if err != nil {
		log.Printf("latency error %s %s %s", pod.GetName(), node.GetName(), err.Error())
		return false, []string{fmt.Sprintf("Node %s latency could not be retrieved", node.Name)}, nil
	}
	//nodeLatencyNanos := fromSecondsToNano(nodeLatencyMillis)
	//log.Printf("Node %s currently has %f latency-nanos", node.GetName(), nodeLatencyNanos)
	if nodeLatencyMillis <= float64(minTolerableLatencyAsMilli) {
		log.Printf("latency success %s %f >= %s %f", pod.GetName(), float64(minTolerableLatencyAsMilli), node.GetName(), nodeLatencyMillis)
		return true, nil, nil
	} else {
		log.Printf("latency fail %s  %f <= %s %f", pod.GetName(), minTolerableLatencyAsMilli, node.GetName(), nodeLatencyMillis)
		return false, []string{fmt.Sprintf("Node %s has %f latency while pod only tolerates only up to %f latency", node.Name, nodeLatencyMillis, float64(minTolerableLatencyAsMilli))}, nil
	}
}

func TCPBandwidthPredicate(pod *v1.Pod, node v1.Node) (bool, []string, error) {
	//log.Printf("in TCPBandwidthPredicate")
	bandwidths := getRequests(pod, "example.com/tcp-mbpns")
	if len(bandwidths) == 0 {
		return true, []string{}, nil
	}
	maxRequestedBandwidth := toKilo(findMax(bandwidths))

	//log.Printf("Pod needs at least %d tcp-mbpns", maxRequestedBandwidth)
	nodeBandwidth, err := requestTCPBandwidthMetrics(node.GetName())
	if err != nil {
		log.Printf("TCPBandwidth error %s %s %s", pod.GetName(), node.GetName(), err.Error())
		return false, []string{fmt.Sprintf("Node %s tcp-mbpns could not be retrieved", node.Name)}, nil
	}
	//log.Printf("Node %s currently has %d tcp-mbpns", node.GetName(), nodeBandwidth)
	if float64(nodeBandwidth) >= maxRequestedBandwidth {
		log.Printf("TCPBandwidth success %s  %f <= %s %d", pod.GetName(), maxRequestedBandwidth, node.GetName(), nodeBandwidth)
		return true, nil, nil
	} else {
		log.Printf("TCPBandwidth fail %s  %f >= %s %d", pod.GetName(), maxRequestedBandwidth, node.GetName(), nodeBandwidth)
		return false, []string{fmt.Sprintf("Node %s has %d tcp-mbpns while pod needs at least %f tcp-mbpns", node.Name, nodeBandwidth, maxRequestedBandwidth)}, nil
	}
}

func UDPBandwidthPredicate(pod *v1.Pod, node v1.Node) (bool, []string, error) {
	//log.Printf("in UDPBandwidthPredicate")
	bandwidths := getRequests(pod, "example.com/udp-mbpns")
	if len(bandwidths) == 0 {
		return true, []string{}, nil
	}
	maxRequestedBandwidth := toKilo(findMax(bandwidths))

	//log.Printf("Pod needs at least %d udp-mbpns", maxRequestedBandwidth)
	nodeBandwidth, err := requestUDPBandwidthMetrics(node.GetName())
	if err != nil {
		log.Printf("UDPBandwidth error %s %s %s", pod.GetName(), node.GetName(), err.Error())
		return false, []string{fmt.Sprintf("Node %s udp-mbpns could not be retrieved", node.Name)}, nil
	}
	//log.Printf("Node %s currently has %d udp-mbpns", node.GetName(), nodeBandwidth)
	if float64(nodeBandwidth) >= maxRequestedBandwidth {
		log.Printf("UDPBandwidth success %s %f <= %s %d", pod.GetName(), maxRequestedBandwidth, node.GetName(), nodeBandwidth)
		return true, nil, nil
	} else {
		log.Printf("UDPBandwidth fail %s %f >= %s %d", pod.GetName(), maxRequestedBandwidth, node.GetName(), nodeBandwidth)
		return false, []string{fmt.Sprintf("Node %s has %d udp-mbpns while pod needs at least %f udp-mbpns", node.Name, nodeBandwidth, maxRequestedBandwidth)}, nil
	}
}

func JitterPredicate(pod *v1.Pod, node v1.Node) (bool, []string, error) {
	//log.Printf("in JitterPredicate")
	jitters := getRequests(pod, "example.com/jitter")
	if len(jitters) == 0 {
		return true, []string{}, nil
	}
	maxTolerableJitter := findMin(jitters)
	jitterMillis := toMillis(maxTolerableJitter)
	//log.Printf("Pod tolerates up to %f jitter ms", jitterMillis)
	nodeJitter, err := requestJitterMetrics(node.GetName())
	if err != nil {
		log.Printf("jitter error %s %s %s", pod.GetName(), node.GetName(), err.Error())
		return false, []string{fmt.Sprintf("Node %s jitter could not be retrieved", node.Name)}, nil
	}
	//log.Printf("Node %s currently has %d jitter ms", node.GetName(), nodeJitter)
	if float64(nodeJitter) <= jitterMillis {
		log.Printf("jitter success %s %f >= %s %f", pod.GetName(), jitterMillis, node.GetName(), float64(nodeJitter))
		return true, nil, nil
	} else {
		log.Printf("jitter fail %s %f >= %s %f", pod.GetName(), jitterMillis, node.GetName(), float64(nodeJitter))
		return false, []string{fmt.Sprintf("Node %s has %d jitter ms while pod only tolerates only up to %f jitter ms", node.Name, nodeJitter, jitterMillis)}, nil
	}
}

func getRequests(pod *v1.Pod, resource v1.ResourceName) []int64 {
	requests := make([]int64, 0, 3)
	for _, container := range pod.Spec.Containers {
		val, ok := container.Resources.Requests[resource]
		if ok {
			requests = append(requests, val.MilliValue())
		}
	}
	return requests
}

func findMin(requests []int64) int64 {
	sort.Slice(requests, func(i, j int) bool {
		return requests[i] < requests[j]
	})
	return requests[0]
}

func findMax(requests []int64) int64 {
	sort.Slice(requests, func(i, j int) bool {
		return requests[i] > requests[j]
	})
	return requests[0]
}

func toNano(latencyMillis int64) float64 {
	return float64(latencyMillis) * 0.001
}

func toKilo(tcpMillis int64) float64 {
	return float64(tcpMillis) * 0.001
}

func toMillis(jitterMillis int64) float64 {
	return float64(jitterMillis) * 0.001
}

func fromSecondsToNano(latencyMillis float64) float64 {
	return float64(latencyMillis) * 1000000000
}
