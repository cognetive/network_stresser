## Test suite for Skydive

This folder holds specific Skydive test stress code 

### Preqrequisites:

apt-get install python
apt-get install pip
apt-get install bc
pip install pyyaml

HELM_GET=https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get
HELM_VER="v2.9.1"
curl $HELM_GET | sed 's/helm version/helm --debug version/' | bash -s -- --version $HELM_VER

helm init
helm repo add ibm-charts https://raw.githubusercontent.com/IBM/charts/master/repo/stable/

note 1: If you are running the stresser from a pod inside the cluster, you should allow access to k8s from that pod, in order to do that, execute:
'''kubectl create clusterrolebinding default-admin --clusterrole cluster-admin --serviceaccount=default:default'''

note 2: To monitor additional pods (for example Skydive pods that are deployed in diffrent namespace) you can add or change the configuration file '''stats.conf'''. For example:

To monirot also skydive pods under the 'monitoring' namespace, add to the file:

'''monitoring app skydive-ibm-skydive-dev'''

### Usage:

Execute from the CLI:

python run_iperf_tests.py

