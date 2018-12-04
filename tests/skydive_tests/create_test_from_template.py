import os

def replace_line(line,serviceName,external_tcp_port,external_udp_port,internal_tcp_port,internal_udp_port):
    if line.find("serviceName") != -1:
        return "serviceName: "+serviceName+"\n"
    if line.find("tcpPort") != -1:
        return "  tcpPort: "+str(internal_tcp_port)+"\n"
    if line.find("tcpExternalPort") != -1:
        return "  tcpExternalPort: "+str(external_tcp_port)+"\n"
    if line.find("udpPort") != -1:
        return "  udpPort: "+str(internal_udp_port)+"\n"
    if line.find("udpExternalPort") != -1:
        return "  udpExternalPort: "+str(external_udp_port)+"\n"
    return line
def generate_one_test(filename,serviceName,external_tcp_port,external_udp_port,internal_tcp_port,internal_udp_port):
    if serviceName=='receiver':
        external_tcp_port=internal_tcp_port
        external_udp_port=internal_udp_port
    with open(filename,"r") as f:
        lines=f.readlines()
    lines=[replace_line(line,serviceName,external_tcp_port,external_udp_port,internal_tcp_port,internal_udp_port) for line in lines]
    if serviceName!='receiver':
        nodeEnable='true'
    else:
        nodeEnable='false'
    lines.append('  isNodePort: '+nodeEnable+'\n')
    with open(filename.split("/")[1],"w+") as f:
        f.writelines(lines)

def create_tests(dir,serviceName,external_tcp_port,external_udp_port,internal_tcp_port=8081,internal_udp_port=8082):
    templates=os.listdir(dir)
    templates.remove('tests_iperf')
    templates=[os.path.join(dir,filename) for filename in templates]
    for filename in templates:
        generate_one_test(filename,serviceName,external_tcp_port,external_udp_port,internal_tcp_port,internal_udp_port)

