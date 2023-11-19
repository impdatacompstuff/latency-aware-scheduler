package main

import (
	"flag"
	"net/http"
	"os"

	"github.com/emicklei/go-restful"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/component-base/logs"
	"k8s.io/klog/v2"

	openapinamer "k8s.io/apiserver/pkg/endpoints/openapi"
	genericapiserver "k8s.io/apiserver/pkg/server"

	fakeprov "metrics.server/custom/provider"
	"sigs.k8s.io/custom-metrics-apiserver/pkg/apiserver"
	basecmd "sigs.k8s.io/custom-metrics-apiserver/pkg/cmd"
	"sigs.k8s.io/custom-metrics-apiserver/pkg/provider"
	generatedopenapi "sigs.k8s.io/custom-metrics-apiserver/test-adapter/generated/openapi"
)

type SampleAdapter struct {
	basecmd.AdapterBase

	// Message is printed on succesful startup
	Message string
}

func (a *SampleAdapter) makeProviderOrDie() (provider.MetricsProvider, *restful.WebService) {
	client, err := a.DynamicClient()
	if err != nil {
		klog.Fatalf("unable to construct dynamic client: %v", err)
	}

	mapper, err := a.RESTMapper()
	if err != nil {
		klog.Fatalf("unable to construct discovery REST mapper: %v", err)
	}

	return fakeprov.NewFakeProvider(client, mapper)
}

func main() {
	logs.InitLogs()
	defer logs.FlushLogs()
	klog.InitFlags(nil)

	cmd := &SampleAdapter{}

	cmd.OpenAPIConfig = genericapiserver.DefaultOpenAPIConfig(generatedopenapi.GetOpenAPIDefinitions, openapinamer.NewDefinitionNamer(apiserver.Scheme))
	cmd.OpenAPIConfig.Info.Title = "test-adapter"
	cmd.OpenAPIConfig.Info.Version = "1.0.0"

	cmd.Flags().StringVar(&cmd.Message, "msg", "starting adapter...", "startup message")
	cmd.Flags().AddGoFlagSet(flag.CommandLine) // make sure we get the klog flags
	cmd.Flags().Parse(os.Args)

	testProvider, webService := cmd.makeProviderOrDie()
	cmd.WithCustomMetrics(testProvider)
	cmd.WithExternalMetrics(testProvider)

	klog.Infof(cmd.Message)
	// Set up POST endpoint for writing fake metric values
	restful.DefaultContainer.Add(webService)
	go func() {
		// Open port for POSTing fake metrics
		klog.Fatal(http.ListenAndServe(":8080", nil))
	}()
	if err := cmd.Run(wait.NeverStop); err != nil {
		klog.Fatalf("unable to run custom metrics adapter: %v", err)
	}
}
