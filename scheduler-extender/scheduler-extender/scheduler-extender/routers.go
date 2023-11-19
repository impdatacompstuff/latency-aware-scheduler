package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"

	"github.com/julienschmidt/httprouter"
	schedulerapi "k8s.io/kube-scheduler/extender/v1"
)

func Index(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
	fmt.Fprint(w, "Welcome to sample-scheduler-extender!\n")
}

func Filter(w http.ResponseWriter, r *http.Request, ps httprouter.Params) {
	//log.Println("In filter endpoint")
	var buf bytes.Buffer
	body := io.TeeReader(r.Body, &buf)
	//log.Printf("Received data: %#v", body)

	var extenderArgs schedulerapi.ExtenderArgs
	var extenderFilterResult *schedulerapi.ExtenderFilterResult
	if err := json.NewDecoder(body).Decode(&extenderArgs); err != nil {
		extenderFilterResult = &schedulerapi.ExtenderFilterResult{
			Error: err.Error(),
		}
	} else {
		//log.Printf("Decoded data: %#v", extenderArgs)
		extenderFilterResult = filter(extenderArgs)
	}

	if response, err := json.Marshal(extenderFilterResult); err != nil {
		log.Fatalln(err)
	} else {
		//log.Printf("%#v", response)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write(response)
	}
}

func Prioritize(w http.ResponseWriter, r *http.Request, ps httprouter.Params) {
	log.Println("In prioritize endpoint")
	var buf bytes.Buffer
	body := io.TeeReader(r.Body, &buf)
	log.Printf("Received data: %#v", body)
	var extenderArgs schedulerapi.ExtenderArgs
	var hostPriorityList *schedulerapi.HostPriorityList
	if err := json.NewDecoder(body).Decode(&extenderArgs); err != nil {
		log.Println(err)
		hostPriorityList = &schedulerapi.HostPriorityList{}
	} else {
		log.Printf("Decoded data: %#v", extenderArgs)
		hostPriorityList = prioritize(extenderArgs)
		log.Printf("%#v", hostPriorityList)
	}

	if response, err := json.Marshal(hostPriorityList); err != nil {
		log.Fatalln(err)
	} else {
		log.Printf("%#v", response)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write(response)
	}
}

// func Bind(w http.ResponseWriter, r *http.Request, ps httprouter.Params) {}
