import os
import subprocess
from time import sleep
import logging
import yaml
import mmap
import re

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
ENV_VARIABLE_NAME = conf_vars.get('envVariableName', "SKYDIVE_ANALYZER_STARTUP_CAPTURE_GREMLIN")
RUN_FOREVER = conf_vars.get('runForever', True)
ANALYZE_TEST_RESULTS = conf_vars.get('analyzeTestResults', True)
TEST_OUTPUT_DIRECTORY = conf_vars.get('testsOutputDirectory', "/output")
ANALYZED_RESULTS_CSV = conf_vars.get('analyzedResultsFileName', "analyzedResults.csv")

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


def install_skydive_helm_chart(env_var_meaning, env_var_value):
    """
    Install SkyDive helm chart.
    :param env_var_meaning: Meaning of the ENV variable configuration
    :param env_var_value: SkyDive chart configuration value for ENV. variable: "ENV_VARIABLE_NAME"
    """
    logging.info("Installing SkyDive helm chart, with configuration of: \"{}\".".format(env_var_meaning))
    subprocess.call("helm install {} --name={} --set env[0].name=\"{}\" --set env[0].value=\"{}\"".
                    format(SKYDIVE_HELM_CHART_PATH, SKYDIVE_HELM_CHART_NAME,
                           ENV_VARIABLE_NAME, env_var_value), shell=True)

def cleaning_tests_output_directory():
    """
    Cleaning tests output directoy
    """
    logging.info("Cleaning tests output directoy \"{}\".".format(SCRIPT_PATH + TEST_OUTPUT_DIRECTORY))
    subprocess.call("rm -R -f {}".format(SCRIPT_PATH + TEST_OUTPUT_DIRECTORY), shell=True)

def avarage (theList):
    intlist = [int(s) for s in theList]
    if len(intlist) == 0:
        return 0
    
    return (sum(intlist) / len(intlist))
    
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
    
    skydiveAgentsCPUasList = re.findall("pod:skydive-ibm-skydive-dev-agent.*CPU:(.*)m", stats)
    skydiveAnalyzerCPUasList = re.findall("pod:skydive-ibm-skydive-dev-analyzer.*CPU:(.*)m", stats)
    receiverCPUasList = re.findall("pod:receiver.*CPU:(.*)m", stats)
    generatorCPUasList = re.findall("pod:generator.*CPU:(.*)m", stats)
    
    skydiveAgentsMEMasList = re.findall("pod:skydive-ibm-skydive-dev-agent.*RAM:(.*)Mi", stats)
    skydiveAnalyzerMEMasList = re.findall("pod:skydive-ibm-skydive-dev-analyzer.*RAM:(.*)Mi", stats)
    receiverMEMasList = re.findall("pod:receiver.*RAM:(.*)Mi", stats)
    generatoMEMasList = re.findall("pod:generator.*RAM:(.*)Mi", stats)
    
    resultsFormatedInCSV = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(skydiveType,testName,startTime,endTime,totalTime,flows,flowsPerSecond,
                 avarage(skydiveAgentsCPUasList),avarage(skydiveAnalyzerCPUasList),avarage(receiverCPUasList),avarage(generatorCPUasList),
                 min(skydiveAgentsCPUasList),min(skydiveAnalyzerCPUasList),min(receiverCPUasList),min(generatorCPUasList),
                 max(skydiveAgentsCPUasList),max(skydiveAnalyzerCPUasList),max(receiverCPUasList),max(generatorCPUasList),
                 avarage(skydiveAgentsMEMasList),avarage(skydiveAnalyzerMEMasList),avarage(receiverMEMasList),avarage(generatoMEMasList),
                 min(skydiveAgentsMEMasList),min(skydiveAnalyzerMEMasList),min(receiverMEMasList),min(generatoMEMasList),
                 max(skydiveAgentsMEMasList),max(skydiveAnalyzerMEMasList),max(receiverMEMasList),max(generatoMEMasList)
                 )
    logging.info("------------")
    logging.info("TEST RESULTS")
    logging.info("------------")
    logging.info("\n"+ TEST_RESULTS_CSV_HEADER + "\n"+ resultsFormatedInCSV)
    with open(CURRENT_PATH+ANALYZED_RESULTS_CSV, "ab") as resultsfile:
        resultsfile.write(resultsFormatedInCSV+"\n")
    
if __name__ == "__main__":
    
    skydive_charts_config_dict = dict()  # type: dict
    skydive_charts_config_dict["Monitor_all_except_loopbacks"] = "G.V().has(\'Name\'\,NE(\'lo\'))"
    skydive_charts_config_dict["Monitor_only_host_interfaces"] = "G.V().has(\'Name\'\,NE(\'lo\')).has(\'Type\'\,\'device\')"
    skydive_charts_config_dict["not_monitoring"] = ""
    clean_existed_skydive_helm_chart()

    if ANALYZE_TEST_RESULTS:
      with open(CURRENT_PATH+ANALYZED_RESULTS_CSV, "wb") as resultsfile:
          resultsfile.write(TEST_RESULTS_CSV_HEADER+"\n")                    

    while True:
        for env_variable_meaning, env_variable_value in skydive_charts_config_dict.iteritems():
            test_file_number = 0  # type: int
            install_skydive_helm_chart(env_variable_meaning, env_variable_value)

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
                    analyze_test_results(env_variable_meaning,filename[:-10])
                  
            clean_existed_skydive_helm_chart()
        if not RUN_FOREVER:
          break
          
