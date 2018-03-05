## Test suite for Kubernetes

This test suite consists of a Helm charts for network bandwith testing a Kuberntes cluster, the required files to create the relevant Docker image and a testing and monitoring automation.

The structure of the stresser package looks a follows:
````
network_stresser/
├── network_stresser_image/
│   ├── Dockerfile
│   ├── utils.py
│   ├── traffic_generator.py
│   ├── traffic_receiver.py
│   ├── traffic_receiver_tcp.py
│   └── traffic_receiver_udp.py
├── stable/
│   ├── network-stresser/
│   │   ├── templates/
│   │   │   ├── NOTES.txt
│   │   │   ├── stresser-generator-rc.yml
│   │   │   ├── stresser-receiver-rc.yml
│   │   │   └── stresser-receiver-svc.yml
│   │   ├── Chart.yaml
│   │   └── values.yaml
│   └── Readme.md
├── tests/
│   ├── large_test.yaml
│   ├── medium_test.yaml
│   ├── small_test.yaml
│   ├── stats.conf
│   └── test.sh
└── README.md
```` 

### Preqrequisites:

First, clone the repository:
````
> git clone https://github.com/cognetive/network_stresser
> cd network_stresser
````

### Using the chart:

To install the chart execute:
```` 
> helm install stable/network-stresser --name=network-stresser
```` 
For further information, follow the [instructions for using the helm chart](stable/Readme.md) in order to run and configure the test.

### Using the automated tests:

In the [tests](tests) directory you will find an automation which runs a custom test while monitoring the cluster.
In this directory there are 3 pre-confgiured tests - small, medium and large. These define various levels of stress to inflict on the cluster.
To run a test based on one of these stock sets of parameters, run the following:
````
> ./test.sh <test_name>
````
where test_name is small, medium or large.
You can also run the test in debug mode, which will allow you to monitor its progress, by running:
````
> ./test.sh debug <test_name>
````

By default, all the pods used in the test are monitored (for CPU and RAM usage) during the test. You can change this (and add monitored pods of your own) by modifying the [stats configuration file](tests/stats.conf). Instructions of how to properly modify the configuration can be found in the file itself.

The output of the test can be found in the output directory (which is not cleared between tests).
There you will find a file for every pod used in the test (traffic generators and receivers) which contains its logs.
You will also find a stats.log file (also not cleared between tests, it will gather information until manually deleted) which will have the following information:
- A TEST_STARTING line at the beginning of every test, summarising the main test paramters specified
- A TEST_COMPLETE line at the end of everyt test, with statistics of the test: total_runtime, number of flows generated, flows sent per second
- In between those 2 lines, there will be STATS lines, listing CPU and RAM stats for every pod marked for monitoring in the configuration file, gathered every 5 seconds

### Customization

#### Custom images (optional)

The image used in this test by default is the cognetive/network_stresser image in Docker Hub.
You can use a different version of this image by altering the imagePath field in the values file you use.

The Docker file and Python code used do build the standard image are provided in the [image directory](network_stresser_image). You can create a custom version of this image by altering the aforementioned files. After making the desired alterations, login to the container registry, for example for IBM Cloud, perform:
````
> bx cr login
````
Then rebuild and push your image:
````
> cd cognetive-network-stresser/network_stresser_image/
> sudo docker build -t <registry path>/<namespace>/network_stresser:<version> .
> sudo docker push <registry path>/<namespace>/network_stresser:<version>
````
Where the registry name and namespace are those used in your container service, and version is any tag you choose to use.

In order to use your custom image, make sure you change the imagePath field in the values file to match the path of your custom image, i.e.:
````
imagePath: <registry path>/<namespace>/network_stresser:<version>
````

#### Custom tests
To create a new test:
- Create a new yaml file name <test_name>_test.yaml
- Any parameter not specified in this new yaml will be taken from the [default values](stable/network-stresser/values.yaml).
Run the test by executing:
````
> ./test.sh <test_name>
````
As before, debug mode is also available.

