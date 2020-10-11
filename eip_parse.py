import re

replace = {'Communications Adapter (12)': 'Comm Adapter ',
           'Programmable Logic Controller (14)': 'PLC ',
           'PowerFlex 525 (150)': '',
           'Unknown Device Type (123)': '',
           'Human-Machine Interface (24)': 'HMI ',
           'CIP Motion Drive (37)': 'CIP Motion Drive '}

types = list()

if __name__ == '__main__':
    with open('eip_info.txt', 'r') as f:
        eip_info = f.read()
    for m in re.finditer(r'Nmap scan report for (\d+\.\d+\.\d+\.\d+).{5,100}44818/udp open.*?type: (.*?)\n.*?productName: (.*?)\n',
                         eip_info,
                         re.DOTALL):
        if m.group(2) not in types:
            types.append(m.group(2))
        if m.group(2) == m.group(3):
            output = m.group(1) + '\t' + m.group(2)
        else:
            output = m.group(1) + '\t' + m.group(2) + m.group(3)
        for x in replace.keys():
            output.replace(x, (replace[x]))
        print(output)
    print(types)