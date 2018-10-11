import os
import subprocess
from time import sleep

START_STR = "iperf"
END_STR = "_test.yaml"
SCRIPT_PATH = "/home/gidi/network_stresser/tests/test.sh"
SKYDIVE_HELM_CHART_NAME = "skydive"
DEFAULT_NAMESPACE = "default"
WAIT_TIME_AFTER_CHART_INSTALL_IN_SECONDS = 120

ENV_VARIABLE_NAME = "SKYDIVE_ANALYZER_STARTUP_CAPTURE_GREMLIN"


def clean_existed_skydive_helm_chart():
    """
    Clean skydive helm chart, if existed.
    """
    print("Clearing existed SkyDive helm chart, if existed.")
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
            print("Wait a while for fully removal.")
            sleep(5)
            process = subprocess.Popen(
                "kubectl -n {} get pod -l release={} -o jsonpath=\"{{.items[*].metadata.name}}\"".
                format(DEFAULT_NAMESPACE, SKYDIVE_HELM_CHART_NAME), stdout=subprocess.PIPE, shell=True)
            existed_pods = process.stdout.readline()
            process.terminate()

        print("Successfully cleared existed SkyDive helm chart")


def install_skydive_helm_chart(env_var_meaning, env_var_value):
    """
    Install SkyDive helm chart.
    :param env_var_meaning: Meaning of the ENV variable configuration
    :param env_var_value: SkyDive chart configuration value for ENV. variable: "ENV_VARIABLE_NAME"
    """
    print("\nInstalling SkyDive helm chart, with configuration of: \"{}\".".format(env_var_meaning))
    subprocess.call("helm install ibm-charts/ibm-skydive-dev --name={} "
                    "--set env[0].name=\"{}\" --set env[0].value=\"{}\"".
                    format(SKYDIVE_HELM_CHART_NAME, ENV_VARIABLE_NAME, env_var_value), shell=True)


if __name__ == "__main__":
    skydive_charts_config_dict = dict()  # type: dict
    skydive_charts_config_dict["Monitor_all_except_loopbacks"] = "G.V().has(\'Name\'\,NE(\'lo\'))"

    clean_existed_skydive_helm_chart()
    for env_variable_meaning, env_variable_value in skydive_charts_config_dict.iteritems():
        test_file_number = 0  # type: int
        install_skydive_helm_chart(env_variable_meaning, env_variable_value)

        print("Wait for {} seconds, after chart install.".format(WAIT_TIME_AFTER_CHART_INSTALL_IN_SECONDS))
        sleep(WAIT_TIME_AFTER_CHART_INSTALL_IN_SECONDS)

        # Run all test files for the current installed SkyDive chart
        for filename in os.listdir(os.path.dirname(os.path.abspath(__file__))):
            if filename.endswith(END_STR) and filename.startswith(START_STR):
                test_file_number += 1
                print("Starting to check test file #{}: \"{}\".".format(test_file_number, filename[:-10]))
                subprocess.call("{} {}".format(SCRIPT_PATH, filename[:-10]), shell=True)

        clean_existed_skydive_helm_chart()
