#!/bin/bash

if [[ debug == "$1" ]]; then
  INSTRUMENTING=yes
  shift
fi
echo () {
  [[ "$INSTRUMENTING" ]] && builtin echo $@
}
cd /home/sa-v2customer-dev1
ISTIO_EXPORT=$(./do.sh reconnect | grep export)
cd /home/sa-v2customer-dev
SEC_ADVISOR_EXPORT=$(./do.sh reconnect | grep export)
cd /home/network_stresser1/tests1/
builtin echo $ISTIO_EXPORT
builtin echo $SEC_ADVISOR_EXPORT
#exit 0
CHART_PATH_GEN=/home/network_stresser1/stable1/stable_gen/network-stresser
CHART_PATH_REC=/home/network_stresser1/stable1/stable_rec/network-stresser
CONF_FILE=stats.conf
OUTPUT_DIR=output
LOGFILE=$OUTPUT_DIR/stats.log
CPU_ID=4 # Location of CPU usage value in kubectl top's output
RAM_ID=5 # Location of RAM usage value in kubectl top's output

TEST_NAME=$1
SPECIFIC_TEST_NAME=$(cut -d "/" -f 2 <<< ${TEST_NAME})
RELEASE_GEN=network-stresser-test-${SPECIFIC_TEST_NAME}-gen
RELEASE_REC=network-stresser-test-${SPECIFIC_TEST_NAME}-rec
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
    
    builtin echo $(kubectl get pod -l ${label_key}=${label_val} $args --all-namespaces -o jsonpath="{.items[*].metadata.name}")
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
    builtin echo $(kubectl get pod $1 -n $namespace -o jsonpath="{.status.phase}")
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
            stats=($(kubectl top pod $pod -n $namespace))
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
    helm install ${CHART_PATH_GEN} --name=${RELEASE_GEN} -f ${VALUES}
    $ISTIO_EXPORT
    helm install ${CHART_PATH_REC} --name=${RELEASE_REC} -f ${VALUES}
    $SEC_ADVISOR_EXPORT
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
    echo "removed previous helm relese $release"
}

#=== FUNCTION ==================================================================
# NAME: remove_job
# DESCRIPTION: Delete a kubernetese job
# PARAMETER 1: The job name to remove
#===============================================================================
remove_job() {
    job=$1
    kubectl delete job $job
    pods=$(get_pods job ${job})
    while [ ${#pods} != 0 ]; do
        echo "not yet: $pods still not terminated"
        sleep $REFRESH_RATE
        pods=$(get_pods job ${job})
    done
    echo "removed previous job $job"
}

#=== FUNCTION ==================================================================
# NAME: remove_replicationcontrollers
# DESCRIPTION: Delete a replicationcontrollers job
# PARAMETER 1: The replicationcontrollers name to remove
#===============================================================================
remove_replicationcontrollers() {
    replicationcontrollers=$1
    kubectl delete replicationcontrollers $replicationcontrollers
    pods=$(get_pods app ${replicationcontrollers})
    while [ ${#pods} != 0 ]; do
        echo "not yet: $pods still not terminated"
        sleep $REFRESH_RATE
        pods=$(get_pods app ${replicationcontrollers})
    done
    echo "removed previous replicationcontrollers $replicationcontrollers"
}

#=== FUNCTION ==================================================================
# NAME: remove_service
# DESCRIPTION: Delete a kubernetese service (if exists)
# PARAMETER 1: The service to remove
#===============================================================================
remove_service() {
    service=$1
    kubectl delete service $service
    echo "removed previous service $service, if exists"
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
    
    remove_service receiver
    remove_replicationcontrollers receiver
    remove_job generator
    
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
    $ISTO_EXPORT
    receivers=$(get_pods app receiver)
    for receiver in ${receivers[@]}; do
        save_logs $receiver
    done
    $SEC_ADVISOR_EXPORT
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

# Set "CONF_FILE" to a specific file, if found at test conf file
conf_file_name=$(get_value confFile)
if [ -n "$conf_file_name" ]; then
    CONF_FILE=$conf_file_name
fi
echo "CONF_FILE name is: ${CONF_FILE}"

# Clear the cluster from previous tests
clear_prev_tests
$ISTIO_EXPORT
clear_prev_tests
$SEC_ADVISOR_EXPORT
# Initialise the test
mkdir -p $OUTPUT_DIR
if [ ! -f "$LOGFILE" ]; then
   touch "$LOGFILE"
fi
log "TEST_STARTING, $(get_values)"
install_helm
SECONDS=0
# Wait for the test to complete
sleep 120 # Wait for 2 minutes in order to give enough time to heapster pod to gather relevant stats
wait_for_completion
# Log the final statistics and receivers' output
total_runtime=$SECONDS
log "TEST_COMPLETE, total_runtime=${total_runtime}s, $(gather_statistics)"
save_receivers_logs
# Remove the test helm
remove_helm ${RELEASE_GEN}
$ISTIO_EXPORT
remove_helm ${RELEASE_REC}
$SEC_ADVISOR_EXPORT

builtin echo -e "done\n"
