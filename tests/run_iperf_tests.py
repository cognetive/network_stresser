import os
import subprocess
from time import sleep

START_STR = "iperf"
END_STR = "_test.yaml"
SCRIPT_PATH = "/home/gidi/network_stresser/tests/test.sh"
SKYDIVE_HELM_CHART_NAME = "skydive"
DEFAULT_NAMESPACE = "default"
WAIT_TIME_AFTER_CHART_INSTALL_IN_SECONDS = 120


def clean_existed_skydive_helm_chart():
    """
    Clean skydive helm chart, if existed.
    """
    print("Clearing existed skydive helm chart, if existed.")
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

        print("Successfully cleared existed skydive helm chart")


def install_skydive_helm_chart(env_var_name, env_var_value):
    """
    Install skydive helm chart.
    """
    print("\nInstalling skydive helm chart.")
    subprocess.call("helm install ibm-charts/ibm-skydive-dev --name={} "
                    "--set env[0].name=\"{}\" --set env[0].value=\"{}\"".
                    format(SKYDIVE_HELM_CHART_NAME, env_var_name, env_var_value), shell=True)


if __name__ == "__main__":
    test_file_number = 0  # type: int

    clean_existed_skydive_helm_chart()
    # TODO: Execute the following code for some different skydive helm chart installs, regarding different ENV_VARS

    env_variable_name = "SKYDIVE_ANALYZER_STARTUP_CAPTURE_GREMLIN"  # type: str
    env_variable_value = "G.V().has(\'Name\'\,NE(\'lo\'))"  # type: str
    install_skydive_helm_chart(env_variable_name, env_variable_value)

    print("Wait for {} seconds, after chart install.".format(WAIT_TIME_AFTER_CHART_INSTALL_IN_SECONDS))
    sleep(WAIT_TIME_AFTER_CHART_INSTALL_IN_SECONDS)

    # for filename in os.listdir(os.path.dirname(os.path.abspath(__file__))):
    #     if filename.endswith(END_STR) and filename.startswith(START_STR):
    #         test_file_number += 1
    #         print("Starting to check test file #{}: \"{}\".".format(test_file_number, filename[:-10]))
    #         subprocess.call("{} {}".format(SCRIPT_PATH, filename[:-10]), shell=True)

    # clean_existed_skydive_helm_chart()
