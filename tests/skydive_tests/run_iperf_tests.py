import os
import subprocess
from time import sleep
import logging

# Global variables
START_STR = "iperf"
END_STR = "_test.yaml"
TEST_FILE_NAME_PREFIX = "skydive_tests/"
SCRIPT_PATH = os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + os.sep + os.pardir)
SCRIPT_NAME = "/test.sh"
SKYDIVE_HELM_CHART_NAME = "skydive"
SKYDIVE_HELM_CHART_PATH = "ibm-charts/ibm-skydive-dev"
DEFAULT_NAMESPACE = "default"
LOG_FILE_NAME = "iperf_tests.log"
ENV_VARIABLE_NAME = "SKYDIVE_ANALYZER_STARTUP_CAPTURE_GREMLIN"

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

            logging.info("Successfully cleared existed SkyDive helm chart")


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


if __name__ == "__main__":
    skydive_charts_config_dict = dict()  # type: dict
    skydive_charts_config_dict["Monitor_all_except_loopbacks"] = "G.V().has(\'Name\'\,NE(\'lo\'))"

    clean_existed_skydive_helm_chart()
    for env_variable_meaning, env_variable_value in skydive_charts_config_dict.iteritems():
        test_file_number = 0  # type: int
        install_skydive_helm_chart(env_variable_meaning, env_variable_value)

        # Run all test files for the current installed SkyDive chart
        for filename in os.listdir(os.path.dirname(os.path.abspath(__file__))):
            if filename.endswith(END_STR) and filename.startswith(START_STR):
                test_file_number += 1
                filename = TEST_FILE_NAME_PREFIX + filename
                logging.info("Starting to check test file #{}: \"{}\".".format(test_file_number, filename[:-10]))
                default_working_dir = os.getcwd()  # type: str
                os.chdir(SCRIPT_PATH)
                subprocess.call("{} {}".format(SCRIPT_PATH + SCRIPT_NAME, filename[:-10]), shell=True)
                os.chdir(default_working_dir)

        clean_existed_skydive_helm_chart()
