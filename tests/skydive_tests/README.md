## Test suite for Skydive

This folder holds specific Skydive test stress code 

### Preqrequisites:

apt-get install python
apt-get install pip
pip install pyyaml

HELM_GET=https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get
HELM_VER="v2.9.1"
curl $HELM_GET | sed 's/helm version/helm --debug version/' | bash -s -- --version $HELM_VER

helm init
helm repo add ibm-charts https://raw.githubusercontent.com/IBM/charts/master/repo/stable/

note 1: If you are running the stresser from a pod inside the cluster, you should allow access to k8s from that pod, in order to do that, execute:
'''kubectl create clusterrolebinding default-admin --clusterrole cluster-admin --serviceaccount=default:default'''

rem note 2: If Skydive pods (or any other) are deployed in specific namespace, need to change the configuration file '''stats.conf'''. For example
rem   If skydive is deployed in the 'monitoring' namespace:

rem - default app skydive-ibm-skydive-dev
rem + monitoring app skydive-ibm-skydive-dev

### Usage:

Execute from the CLI:

python run_iperf_tests.py

