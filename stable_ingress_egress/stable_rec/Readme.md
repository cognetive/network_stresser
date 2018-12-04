## Test suite for Kubernetes

This test suite consists a Helm charts for network bandwith testing a Kuberntes cluster.
The structure of the stresser chart looks a follows:
````
stable/
├── network-stresser/
│   ├── templates/
│   │   ├── NOTES.txt
│   │   ├── stresser-generator-rc.yml
│   │   ├── stresser-receiver-rc.yml
│   │   └── stresser-receiver-svc.yml
│   ├── Chart.yaml
│   └── values.yaml
└── Readme.md
```` 

### Preqrequisites:

First you must follow the instructions in the [root directory](../README.md)

### Installing the chart:

You can install the stress test by running the following:
```` 
> helm install stable/network-stresser --name=network-stresser
```` 

### Uninstalling the chart:

You can uninstall the stress test by running the following:
````
> helm delete --purge network-stresser
````

### Configuration

The following table lists the configurable parameters of the chart and their default values.

Parameter | Description | Default
--------- | ----------- | -------
`imagePath` | Path to the Docker image | cognetive/network_stresser:0.0.5
`imagePullPolicy` | Whether to Always pull imaged or only IfNotPresent | IfNotPresent
`serviceName` | The name of the receiver's service | receiver
`receiverReplicas` | How many instances if the receiver to create | 1
`generatorReplicas` | How many instances if the generator to create | 1
`pythonPath` | Path to the Python 2.7 binary | /usr/bin/python2.7
`generatorPath` | Path to the traffic generator Python script | /usr/bin/traffic_generator.py
`receiverPath` | Path to the traffic receiver Python script | /usr/bin/traffic_receiver.py
`tcpReceiverPath` | Path to the TCP traffic receiver Python script | /usr/bin/traffic_receiver_tcp.py
`udpReceiverPath` | Path to the UDP traffic receiver Python script | /usr/bin/traffic_receiver_udp.py
`iperfPath` | Path to the iPerf executable | /usr/bin/iperf3
`cmdOptions.useIperf` | use iPerf network stresser | False
`cmdOptions.iperfBandwidth` | iPerf udp bandwidth (100%=unlimited) | 100m
`cmdOptions.iperfThreads` | Number of iperf threads | 1
`cmdOptions.tcpPort` | TCP port of the server | 8081
`cmdOptions.udpPort` | UDP port of the server | 8082
`cmdOptions.udpPercentage` | The percentage of the flows to be created over UDP (0 to 100) | 50
`cmdOptions.minBytes` | Minimum number of bytes to send in a flow | 100
`cmdOptions.maxBytes` | Maximum number of bytes to send in a flow | 1000
`cmdOptions.udpBuffer` | UDP buffer size (in bytes) | 2000
`cmdOptions.numOfFlows` | Minimum number of flows to generate *(N/A for iPerf)  | 20
`cmdOptions.time` | Minimum length of time to generate traffic (in minutes) | 1
`cmdOptions.delay` | Delay between flows (in milliseconds) | 500
`cmdOptions.silent` | Suppress output | False
