import argparse
import os

def modify_receiver_ports(external_tcp_port,external_udp_port):
    with open('../../stable_ingress_egress/stable_rec/network-stresser/templates/stresser-receiver-svc.yml',"r") as f:
        lines=f.readlines()
    ctr=0
    modified_lines=[]
    for line in lines:
        if line.find('nodePort') == -1:
            modified_lines.append(line)
        elif ctr==0:
            modified_lines.append("    nodePort: "+str(external_tcp_port)+"\n")
            ctr+=1
        else:
            modified_lines.append("    nodePort: "+str(external_udp_port)+"\n")
    with open('../../stable_ingress_egress/stable_rec/network-stresser/templates/stresser-receiver-svc.yml',"w+") as f:
        f.writelines(modified_lines)

def replace_line(line,serviceName,external_tcp_port,external_udp_port):
    if line.find("serviceName") != -1:
        return "serviceName: "+serviceName+"\n"
    if line.find("tcpPort") != -1:
        if serviceName == "receiver":
            return "  tcpPort: 8081\n"
        else:
            return "  tcpPort: "+str(external_tcp_port)+"\n"
    if line.find("udpPort") != -1:
        if serviceName == "receiver":
            return "  udpPort: 8082\n"
        else:
            return "  udpPort: "+str(external_udp_port)+"\n"
    return line
def generate_one_test(filename,serviceName,external_tcp_port,external_udp_port):
    with open(filename,"r") as f:
        lines=f.readlines()
    lines=[replace_line(line,serviceName,external_tcp_port,external_udp_port) for line in lines]
    with open(filename.split("/")[1],"w+") as f:
        f.writelines(lines)

def create_tests(dir,serviceName,external_tcp_port,external_udp_port):
    templates=os.listdir(dir)
    templates=[os.path.join(dir,filename) for filename in templates]
    for filename in templates:
        generate_one_test(filename,serviceName,external_tcp_port,external_udp_port)
    if serviceName != "receiver":
        modify_receiver_ports(external_tcp_port,external_udp_port)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('--d')
    parser.add_argument('--name')
    parser.add_argument('--t')
    parser.add_argument('--u')
    args=parser.parse_args()
    create_tests(args.d,args.name,args.t,args.u)
