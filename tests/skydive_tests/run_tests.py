import os
import subprocess
from time import sleep
import logging
import yaml
import mmap
import re
import json

conf_vars = yaml.load(open('tests_conf.yaml'))

# Global variables
START_STR = conf_vars.get('startStr', "iperf")
END_STR = conf_vars.get('endStr', "_test.yaml")
TEST_FILE_NAME_PREFIX = conf_vars.get('testFileNamePrefix', "skydive_tests/")
SCRIPT_NAME = conf_vars.get('scriptName', "/test.sh")
SKYDIVE_HELM_CHART_NAME = conf_vars.get('skydiveHelmChartName', "skydive")
SKYDIVE_HELM_CHART_PATH = conf_vars.get('skydiveHelmChartPath', "ibm-charts/ibm-skydive-dev")
DEFAULT_NAMESPACE = conf_vars.get('defaultNamespace', "default")
LOG_FILE_NAME = conf_vars.get('logFileName', "iperf_tests.log")
CAPTURE_TYPE_VAR = conf_vars.get('skydiveCaptureTypeEnvVar', "SKYDIVE_ANALYZER_STARTUP_CAPTURE_TYPE")
CAPTURE_GREMLIN_VAR = conf_vars.get('skydiveCaptureGremlinEnvVar', "SKYDIVE_ANALYZER_STARTUP_CAPTURE_GREMLIN")
RUN_FOREVER = conf_vars.get('runForever', True)
ANALYZE_TEST_RESULTS = conf_vars.get('analyzeTestResults', True)
TEST_OUTPUT_DIRECTORY = conf_vars.get('testsOutputDirectory', "/output")
ANALYZED_RESULTS_CSV = conf_vars.get('analyzedResultsFileName', "analyzedResults.csv")
SKYDIVE_CHARTS_DICT =  conf_vars.get('skydiveChartsDict', """{"1-ebpf": "G.V().has('Name'\\\\,NE('lo')).has('Type'\\\\,'device')", "2-Monitor-only-host_interfaces": "G.V().has('Name'\\\\,NE('lo')).has('Type'\\\\,'device')", "3-no-skydive": "", "4-not-monitoring": "", "5-Monitor-all-except_loopbacks": "G.V().has('Name'\\\\,NE('lo'))"}""")
SKYDIVE_AGENT_POD_NAME = conf_vars.get('skydiveAgentPodName',"skydive-ibm-skydive-dev-agent")
SKYDIVE_ANALYZER_POD_NAME = conf_vars.get('skydiveAnalyzerPodName',"skydive-ibm-skydive-dev-analyzer")
SKYDIVE_IMAGE_REPOSITORY = conf_vars.get('skydiveImageRepository',"ibmcom/skydive")
SKYDIVE_IMAGE_TAG = conf_vars.get('skydiveImageTag',"latest")

CURRENT_PATH = os.path.normpath(os.path.dirname(os.path.abspath(__file__))) + os.sep
SCRIPT_PATH = CURRENT_PATH + os.pardir

TEST_RESULTS_CSV_HEADER = ("skydiveType,testName,testStart,testEnd,totalTime,flows,flowsPerSecond,"
    "skydiveAgentsCPUAvg,skydiveAnalyzerCPUAvg,receiverCPUAvg,generatorCPUAvg,"
    "skydiveAgentsCPUMin,skydiveAnalyzerCPUmin,receiverCPUMin,generatorCPUMin,"
    "skydiveAgentsCPUMax,skydiveAnalyzerCPUmax,receiverCPUMax,generatorCPUMax,"
    "skydiveAgentsMEMAvg,skydiveAnalyzerMEMAvg,receiverMEMAvg,generatorMEMAvg,"
    "skydiveAgentsMEMMin,skydiveAnalyzerMEMmin,receiverMEMMin,generatorMEMMin,"
    "skydiveAgentsMEMMax,skydiveAnalyzerMEMmax,receiverMEMMax,generatorMEMMax")

# Set up logging to file
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%d/%m/%y %H:%M:%S',
                    filename=LOG_FILE_NAME)

# Define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# Set a simple format for console use
formatter = logging.Formatter('%(levelname)-8s: %(message)s')
console.setFormatter(formatter)

# Add the handler to the root logger
logging.getLogger('').addHandler(console)


def clean_existed_skydive_helm_chart():
    """
    Clean skydive helm chart, if existed.
    """
    logging.info("Clearing existed SkyDive helm chart, if existed.")
    process = subprocess.Popen("helm list | grep {}".format(SKYDIVE_HELM_CHART_NAME),
                               stdout=subprocess.PIPE, shell=True)
    existed_chart = process.stdout.readline()
    process.terminate()

    if existed_chart:
        subprocess.call("helm delete --purge {}".format(SKYDIVE_HELM_CHART_NAME), shell=True)
        process = subprocess.Popen(
            "kubectl -n {} get pod -l release={} -o jsonpath=\"{{.items[*].metadata.name}}\"".
            format(DEFAULT_NAMESPACE, SKYDIVE_HELM_CHART_NAME), stdout=subprocess.PIPE, shell=True)
        existed_pods = process.stdout.readline()
        process.terminate()

        while existed_pods:
            logging.info("Wait a while for fully removal.")
            sleep(5)
            process = subprocess.Popen(
                "kubectl -n {} get pod -l release={} -o jsonpath=\"{{.items[*].metadata.name}}\"".
                format(DEFAULT_NAMESPACE, SKYDIVE_HELM_CHART_NAME), stdout=subprocess.PIPE, shell=True)
            existed_pods = process.stdout.readline()
            process.terminate()

    logging.info("Successfully cleared existed SkyDive helm chart, if existed.")


def install_skydive_helm_chart(description, gremlin_expr):
    """
    Install SkyDive helm chart.
    :param description: Meaning of the configuration
    :param gremlin_expr: SkyDive chart configuration value for gremlin exprssion.
    """
    captureType = "pcap"
    if description == "no-skydive":
        logging.info("Running test when skydive is not installed (not deployment of Skydive Helm: \"{}\".".format(description))
        return
    
    if description == "ebpf":
        captureType = "ebpf"

    helmCommand = "helm install {} --name={} --set image.repository={} --set image.tag={} --set env[0].name=\"{}\" --set env[0].value=\"{}\" --set env[1].name=\"{}\" --set env[1].value=\"{}\" ".format(SKYDIVE_HELM_CHART_PATH, SKYDIVE_HELM_CHART_NAME, SKYDIVE_IMAGE_REPOSITORY, SKYDIVE_IMAGE_TAG, CAPTURE_GREMLIN_VAR, gremlin_expr, CAPTURE_TYPE_VAR ,captureType)
    logging.info("Installing SkyDive \"{}\" using: {}".format(description, helmCommand))
    subprocess.call(helmCommand, shell=True)

def cleaning_tests_output_directory():
    """
    Cleaning tests output directoy
    """
    logging.info("Cleaning tests output directoy \"{}\".".format(SCRIPT_PATH + TEST_OUTPUT_DIRECTORY))
    subprocess.call("rm -R -f {}".format(SCRIPT_PATH + TEST_OUTPUT_DIRECTORY), shell=True)

def avarage (theList):
    try:
      intlist = [int(s) for s in theList]
      if len(intlist) == 0:
          return 0
    except:
        return 0
    
    return (sum(intlist) / len(intlist))

def maximum (value):
    try:
        themax = max (value)
    except:
        return 0
        
    return themax

def minimum (value):
    try:
        themin = min (value)
    except:
        return 0
        
    return themin
    
def analyze_test_results(skydiveType,testName):
    """
    Analyze test results
    """
    logging.info("Analyzing last test results")
    STATS_FILE_NAME = SCRIPT_PATH + TEST_OUTPUT_DIRECTORY+"/stats.log"
    statsfile = open(STATS_FILE_NAME)
    stats = mmap.mmap(statsfile.fileno(), 0, access=mmap.ACCESS_READ)
    
    startTime = re.findall("time:(.*), TEST_STARTING", stats)[0]
    endTime = re.findall("time:(.*), TEST_COMPLETE", stats)[0]
    totalTime = re.findall("total_runtime=(.*)s,", stats)[0]
    flows = re.findall("flows:(.*),", stats)[0]
    flowsPerSecond = re.findall("flows_per_sec:(.*)", stats)[0]
    
    skydiveAgentsCPUasList = re.findall("pod:{}.*CPU:(.*)m".format(SKYDIVE_AGENT_POD_NAME), stats)
    skydiveAnalyzerCPUasList = re.findall("pod:{}.*CPU:(.*)m".format(SKYDIVE_ANALYZER_POD_NAME), stats)
    receiverCPUasList = re.findall("pod:receiver.*CPU:(.*)m", stats)
    generatorCPUasList = re.findall("pod:generator.*CPU:(.*)m", stats)
    
    skydiveAgentsMEMasList = re.findall("pod:{}.*RAM:(.*)Mi".format(SKYDIVE_AGENT_POD_NAME), stats)
    skydiveAnalyzerMEMasList = re.findall("pod:{}.*RAM:(.*)Mi".format(SKYDIVE_ANALYZER_POD_NAME), stats)
    receiverMEMasList = re.findall("pod:receiver.*RAM:(.*)Mi", stats)
    generatoMEMasList = re.findall("pod:generator.*RAM:(.*)Mi", stats)
    
    resultsFormatedInCSV = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(skydiveType,testName,startTime,endTime,totalTime,flows,flowsPerSecond,
                 avarage(skydiveAgentsCPUasList),avarage(skydiveAnalyzerCPUasList),avarage(receiverCPUasList),avarage(generatorCPUasList),
                 minimum(skydiveAgentsCPUasList),minimum(skydiveAnalyzerCPUasList),minimum(receiverCPUasList),minimum(generatorCPUasList),
                 maximum(skydiveAgentsCPUasList),maximum(skydiveAnalyzerCPUasList),maximum(receiverCPUasList),maximum(generatorCPUasList),
                 avarage(skydiveAgentsMEMasList),avarage(skydiveAnalyzerMEMasList),avarage(receiverMEMasList),avarage(generatoMEMasList),
                 minimum(skydiveAgentsMEMasList),minimum(skydiveAnalyzerMEMasList),minimum(receiverMEMasList),minimum(generatoMEMasList),
                 maximum(skydiveAgentsMEMasList),maximum(skydiveAnalyzerMEMasList),maximum(receiverMEMasList),maximum(generatoMEMasList)
                 )
    logging.info("------------")
    logging.info("TEST RESULTS")
    logging.info("------------")
    logging.info("\n"+ TEST_RESULTS_CSV_HEADER + "\n"+ resultsFormatedInCSV)
    with open(CURRENT_PATH+ANALYZED_RESULTS_CSV, "ab") as resultsfile:
        resultsfile.write(resultsFormatedInCSV+"\n")
    
if __name__ == "__main__":
    
    skydive_charts_config_dict = json.loads(SKYDIVE_CHARTS_DICT)
    logging.info("Using Skydive configurations {}".format(skydive_charts_config_dict))

    clean_existed_skydive_helm_chart()
    
    if ANALYZE_TEST_RESULTS:
      with open(CURRENT_PATH+ANALYZED_RESULTS_CSV, "wb") as resultsfile:
          resultsfile.write(TEST_RESULTS_CSV_HEADER+"\n")                    

    while True:
        for description, gremlin_expr in sorted(skydive_charts_config_dict.iteritems()):
            test_file_number = 0  # type: int
            install_skydive_helm_chart(description, gremlin_expr)

            # Run all test files for the current installed SkyDive chart
            for filename in sorted(os.listdir(os.path.dirname(os.path.abspath(__file__)))):
                if filename.endswith(END_STR) and filename.startswith(START_STR):
                  test_file_number += 1
                  if ANALYZE_TEST_RESULTS:
                    cleaning_tests_output_directory()
                  filename = TEST_FILE_NAME_PREFIX + filename
                  logging.info("Starting to check test file #{}: \"{}\".".format(test_file_number, filename[:-10]))
                  default_working_dir = os.getcwd()  # type: str
                  os.chdir(SCRIPT_PATH)
                  subprocess.call("{} {}".format(SCRIPT_PATH + SCRIPT_NAME, filename[:-10]), shell=True)
                  os.chdir(default_working_dir)
                  if ANALYZE_TEST_RESULTS:
                    analyze_test_results(description,filename[:-10])
                  
            clean_existed_skydive_helm_chart()
        if not RUN_FOREVER:
          break
          
