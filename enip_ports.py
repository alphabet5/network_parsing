import re

# replace = {'Communications Adapter (12)': 'Comm Adapter ',
#            'Programmable Logic Controller (14)': 'PLC ',
#            'PowerFlex 525 (150)': '',
#            'Unknown Device Type (123)': '',
#            'Human-Machine Interface (24)': 'HMI ',
#            'CIP Motion Drive (37)': 'CIP Motion Drive '}
#
# types = list()


from collections import defaultdict

def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


if __name__ == '__main__':
    with open('enip-info3.xml', 'r') as f:
        eip_info = f.read()
    from xml.etree import cElementTree as ET
    devices = list()
    e = ET.XML(eip_info)
    d = etree_to_dict(e)
    for device in d['nmaprun']['host']:
        if device['status']['@state'] == 'up':
            if 'port' in device['ports']:
                output = dict()
                if type(device['address']) == list:
                    addresses = device['address']
                else:
                    addresses = [device['address']]
                for addr in addresses:
                    if addr['@addrtype'] == 'ipv4':
                        output['ip'] = addr['@addr']
                ports_list = list()
                if type(device['ports']['port']) == list:
                    ports = device['ports']['port']
                else:
                    ports = [device['ports']['port']]
                for port in ports:
                    if port['state']['@state'] == 'open':
                        if port['service']['@name'] == 'unknown':
                            ports_list.append(port['@protocol'] + port['@portid'])
                        else:
                            ports_list.append(port['service']['@name'])

                output['ports'] = ','.join(ports_list)
                print(output['ip'] + '\t' + output['ports'])
    #         if device['ports']['port']['state']['@state'] == 'open':
    #             if device['ports']['port']['script']['@output'] != '':
    #                 output = dict()
    #                 output['enip'] = device['ports']['port']['script']['@output']
    #                 # break
    #                 # for addr in device['address']:
    #                 #     if addr['@addrtype'] == 'ipv4':
    #                 #         output['ip'] = addr['@addr']
    #                 #     if addr['@addrtype'] == 'mac':
    #                 #         output['mac'] = addr['@addr']
    #                 for elem in device['ports']['port']['script']['elem']:
    #                     output[elem['@key']] = elem['#text']
    #                 devices.append(output)
    #             else:
    #                 print("device['ports']['port']['script']['@output']")
    #                 print(device['ports']['port']['script']['@output'])
    #         else:
    #             print("device['ports']['port']['state']['@state']")
    #             print(device['ports']['port']['state']['@state'])
    #     else:
    #         print("device['status']['@state']")
    #         print(device['status']['@state'])
    #
    # for d in devices:
    #     print('\t'.join(
    #         [d['deviceIp'], d['vendor'], d['productName'], 'Ethernet/IP', d['type'], d['revision'], d['vendor']]))
    #
    #




    # for m in re.finditer(r'Nmap scan report for (\d+\.\d+\.\d+\.\d+).{5,100}44818/udp open.*?type: (.*?)\n.*?productName: (.*?)\n',
    #                      eip_info,
    #                      re.DOTALL):
    #     if m.group(2) not in types:
    #         types.append(m.group(2))
    #     if m.group(2) == m.group(3):
    #         output = m.group(1) + '\t' + m.group(2)
    #     else:
    #         output = m.group(1) + '\t' + m.group(2) + '\t' + m.group(3)
    #     for x in replace.keys():
    #         output.replace(x, (replace[x]))
    #     print(output)
    # print(types)