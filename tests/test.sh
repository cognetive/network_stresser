#!/bin/bash

if [[ debug == "$1" ]]; then
  INSTRUMENTING=yes
  shift
fi
echo () {
  [[ "$INSTRUMENTING" ]] && builtin echo $@
}


CHART_PATH=../stable/network-stresser/
CONF_FILE=stats.conf
OUTPUT_DIR=output
LOGFILE=$OUTPUT_DIR/stats.log
CPU_ID=4 # Location of CPU usage value in kubectl top's output
RAM_ID=5 # Location of RAM usage value in kubectl top's output

TEST_NAME=$1
RELEASE=network-stresser-test-${TEST_NAME}
VALUES=${TEST_NAME}_test.yaml
DEFAULT_NAMESPACE=default
REFRESH_RATE=5s

#=== FUNCTION ==================================================================
# NAME: get_pods
# DESCRIPTION: Get all pods withing a given namespace, filtered by the proivded
#   label
# PARAMETER 1: The label used to filter pods
# PARAMETER 2: The desired value of the label
# PARAMETER 3: Optional. The namespace of the desired pods. Default value is
#   $DEFAULT_NAMESPACE.
# PARAMETER 4: Optional. Extra arguments for kubectl get pods. Default value is
#   empty.
#===============================================================================
get_pods() {
    label_key=$1
    label_val=$2
    namespace=${3:-$DEFAULT_NAMESPACE}
    args=$4
    
    builtin echo $(kubectl -n ${namespace} get pod -l ${label_key}=${label_val} $args -o jsonpath="{.items[*].metadata.name}")
}

#=== FUNCTION ==================================================================
# NAME: get_pod_status
# DESCRIPTION: Get the status of the given pod 
# PARAMETER 1: Optional. The namespace of the desired pod. Default value is
#   $DEFAULT_NAMESPACE.
#===============================================================================
get_pod_status() {
    # Get the status of the given pod 
    pod=$1
    namespace=${2:-$DEFAULT_NAMESPACE}
    builtin echo $(kubectl -n ${namespace} get pods $1 -o jsonpath="{.status.phase}")
}

#=== FUNCTION ==================================================================
# NAME: log
# DESCRIPTION: Add a log entry
# PARAMETER 1: The log entry to add
#===============================================================================
log() {
    builtin echo "test:$TEST_NAME, time:$(date +"%d/%m/%Y %H:%M:%s"), $1" >> $LOGFILE
}

#=== FUNCTION ==================================================================
# NAME: get_value
# DESCRIPTION: Extract a given test paramtere from the values file
# PARAMETER 1: The name of the paramter
#===============================================================================
get_value() {
    builtin echo $(cat ${VALUES} | grep $1 | awk '{print $2}')
}

#=== FUNCTION ==================================================================
# NAME: get_values
# DESCRIPTION: Extract the test paramteres from the values file
#===============================================================================
get_values() {
    runtime=$(bc <<< "$(get_value time) * 60")
    num_of_flows=$(get_value numOfFlows)
    iperf_bw=$(get_value iperfBandwidth)
    delay=$(get_value delay)
    builtin echo "min_runtime:${runtime}s, iperf_bw:${iperf_bw}, min_flows_per_generator:${num_of_flows}, delay:${delay}ms"
}

#=== FUNCTION ==================================================================
# NAME: get_stats
# DESCRIPTION: Log the CPU and RAM usage of every pod set for monitoring in the
#   configuration file
#===============================================================================
get_stats() {
    while read -r namespace label value; do
        [[ "$namespace" =~ ^#.*$ ]] && continue
        pods=$(get_pods $label $value $namespace)
        for pod in ${pods[@]}; do
            stats=($(kubectl -n $namespace top pod $pod))
            cpu=${stats[$CPU_ID]}
            ram=${stats[$RAM_ID]}
            log "STATS, pod:$pod, CPU:$cpu, RAM:$ram"
        done
    done < $CONF_FILE
}

#=== FUNCTION ==================================================================
# NAME: install_helm
# DESCRIPTION: Install the test helm
#===============================================================================
install_helm() {
    helm install ${CHART_PATH} --name=${RELEASE} -f ${VALUES}
}

#=== FUNCTION ==================================================================
# NAME: remove_helm
# DESCRIPTION: Delete and purge a helm installation
# PARAMETER 1: The release name of the helm to remove
#===============================================================================
remove_helm() {
    release=$1
    helm delete --purge $release
    pods=$(get_pods release ${release})
    while [ ${#pods} != 0 ]; do
        echo "not yet: $pods still not terminated"
        sleep $REFRESH_RATE
        pods=$(get_pods release ${release})
    done
    echo "removed previous test $release"
}

#=== FUNCTION ==================================================================
# NAME: clear_prev_tests
# DESCRIPTION: Remove all previous helms related to the stress test
#===============================================================================
clear_prev_tests() {
    echo "Clearing previous tests"
    prev_tests=$(helm list | grep "network-stresser" | awk '{print $1}')
    for prev_test in ${prev_tests[@]}; do
        echo "found previous test $prev_test"
        remove_helm $prev_test
    done
    echo "Done clearing previous tests"
}

#=== FUNCTION ==================================================================
# NAME: wait_for_completion
# DESCRIPTION: Wait for all generators to complete while sampling the stats of
#   all pods set for monitoring. 
#   Between every sample, there is a waiting time of $REFRESH_RATE seconds
#===============================================================================
wait_for_completion() {
    generators=$(get_pods app generator)
    for generator in ${generators[@]}; do
        status=$(get_pod_status ${generator})
        get_stats
        while [ "$status" != "" ] && [ "$status" != "Succeeded" ]; do
            echo "not yet: $generator is $status"
            sleep $REFRESH_RATE
            status=$(get_pod_status ${generator})
            get_stats
        done
        save_logs $generator
    done
}

#=== FUNCTION ==================================================================
# NAME: save_logs
# DESCRIPTION: Save the logs of a given pod to a log file with a matching name
# PARAMETER 1: The pod to save the logs of
#===============================================================================
save_logs() {
    pod=$1
    kubectl logs $pod > ${OUTPUT_DIR}/${pod}.log
}

#=== FUNCTION ==================================================================
# NAME: save_receivers_logs
# DESCRIPTION: Save the logs of all the receivers
#===============================================================================
save_receivers_logs() {
    receivers=$(get_pods app receiver)
    for receiver in ${receivers[@]}; do
        save_logs $receiver
    done
}

#=== FUNCTION ==================================================================
# NAME: get_param
# DESCRIPTION: Extract the value of a given parameter from the summary line of a
#   given generator's log file
# PARAMETER 1: The generator to extract the param from
# PARAMETER 2: The parameter to extract
#===============================================================================
get_param() {
    generator=$1
    param=$2
    builtin echo $(cat $OUTPUT_DIR/${generator}.log | grep "TEST COMPLETE" | grep -o "${param}=[^ ]*" | cut -d "=" -f 2)
}

#=== FUNCTION ==================================================================
# NAME: gather_statistics
# DESCRIPTION: Calculate final statistics (total number of flows and flows per 
#   second) of the test
#===============================================================================
gather_statistics() {
    let total_flows=0
    let flows_per_sec=0
    
    generators=$(get_pods app generator ${DEFAULT_NAMESPACE} "--show-all")
    for generator in ${generators[@]}; do
        total_flows=$(expr $total_flows + $(get_param $generator flows))
        flows_per_sec=$(bc <<< "$flows_per_sec + $(get_param $generator flows_per_sec)")
    done
    
    builtin echo "flows:${total_flows}, flows_per_sec:${flows_per_sec}"
}

if [ $# -eq 0 ]; then
    builtin echo -e "No test name was provided. In order to run tests, use the following command:
    \t\t test.sh <test_name>
where <test_name> matches a <test_name>_test.yaml file in the tests directory. You may also run the test in debug mode, by using:
    \t\t test.sh debug <test_name>.
    "
    exit
fi


# Clear the cluster from previous tests
clear_prev_tests
# Initialise the test
mkdir -p $OUTPUT_DIR
if [ ! -f "$LOGFILE" ]; then
   touch "$LOGFILE"
fi
log "TEST_STARTING, $(get_values)"
install_helm
SECONDS=0
# Wait for the test to complete
wait_for_completion
# Log the final statistics and receivers' output
total_runtime=$SECONDS
log "TEST_COMPLETE, total_runtime=${total_runtime}s, $(gather_statistics)"
save_receivers_logs
# Remove the test helm
remove_helm ${RELEASE}


builtin echo -e "done\n"
