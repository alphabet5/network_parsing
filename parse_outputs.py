from ntc_templates.parse import parse_output
import os
import re

excluded_commands = ['terminal length 0',
                     'show tech-support',
                     'show running-config',
                     ' ',
                     '']


def split_interface(interface):
    try:
        num_index = interface.index(next(x for x in interface if x.isdigit()))
        str_part = interface[:num_index]
        num_part = interface[num_index:]
    except StopIteration:
        return ['', '']
    return [str_part, num_part]


def normalize_interface_names(non_norm_int):
    tmp = split_interface(non_norm_int)
    interface_type = tmp[0].lower()
    port = tmp[1]
    interfaces = [
        [["ethernet", "eth"], "Eth"],
        [["fastethernet", " fastethernet", "fa", "interface fastethernet", "fas "], "Fa"],
        [["gi", "gigabitethernet", "gigabitethernet", "gi", " gigabitethernet", "interface gigabitethernet", "gig "],
         "Gi"],
        [["tengigabitethernet", "te"], "Te"],
        [["port-channel", "po"], "Po"],
        [["serial"], "Ser"],
    ]
    for int_types in interfaces:
        for names in int_types:
            for name in names:
                if interface_type in name:
                    return_this = int_types[1] + port
                    return return_this
    return "normalize_interface_names Failed"


def exp_cmd(input_command):
    import re
    output = list()
    match_list = {'sh.*': 'show',
                  'tec.*': 'tech-support',
                  'ter.*': 'terminal',
                  'int.*': 'interface',
                  'co.*': 'counter',
                  'll.*': 'lldp',
                  'nei.*': 'neighbor',
                  'span.*': 'spanning-tree',
                  'det.*': 'detail',
                  'vl.*': 'vlan',
                  'br.*': 'brief',
                  'er.*': 'error',
                  'ru.*': 'running-config'}
    for word in input_command.split(' '):
        matched = False
        for r, o in match_list.items():
            if re.match(r, word) is not None:
                output.append(o)
                matched = True
        if not matched:
            output.append(word)
    return ' '.join(output)


def get_interface_vlans(config, syntax):
    from ciscoconfparse import CiscoConfParse
    interfaces = list()
    parse = CiscoConfParse(config.splitlines(), syntax=syntax)
    for interface_obj in parse.find_objects('^interface'):
        if not interface_obj.is_virtual_intf:
            interface = {'name': None, 'mode': None, 'access-vlan': None, 'trunk-vlans': None, 'native-vlan': None,
                         'tagged-native-vlan': None}
            interface_name = normalize_interface_names(interface_obj.re_match_typed(r'^interface\s+(\S.+?)$'))
            interface_mode = interface_obj.re_match_iter_typed(r'switchport mode (.*)', recurse=True)
            interface_access_vlan = interface_obj.re_match_iter_typed(r'switchport access vlan (.*)', recurse=True)
            interface_trunk_vlans = interface_obj.re_match_iter_typed(r'switchport trunk allowed vlan.*? (\d.*)',
                                                                      recurse=True).split(',')
            interface_native_vlan = interface_obj.re_match_iter_typed(r'switchport trunk native vlan (\d*)',
                                                                      recurse=True)
            interface_tagged_native_vlan = 'vlan dot1q tag native' in config
            interfaces.append({'name': interface_name,
                               'mode': interface_mode,
                               'access-vlan': interface_access_vlan,
                               'trunk-vlans': interface_trunk_vlans,
                               'native_vlan': interface_native_vlan,
                               'tagged-native-vlan': interface_tagged_native_vlan})
    return interfaces


def get_interface_description(config, syntax, interface_name):
    from ciscoconfparse import CiscoConfParse
    interfaces = list()
    parse = CiscoConfParse(config.splitlines(), syntax=syntax)
    for interface_obj in parse.find_objects('^interface'):
        if not interface_obj.is_virtual_intf:
            if interface_name == normalize_interface_names(interface_obj.re_match_typed(r'^interface\s+(\S.+?)$')):
                return interface_obj.re_match_iter_typed(r'description (.*)', recurse=True)
    return None


def get_ip_from_sh_ip_int_br(show_ip_int_br):
    for int in show_ip_int_br:
        if int['ipaddr'] != 'unassigned':
            return int['ipaddr']


def get_sh_tech_sub_commands(show_tech_input):
    import re
    commands = dict()
    for cmd in re.finditer(r'.*?-+ (show .*?) -+\n(.*?)(?=-+ show)',
                           show_tech_input,
                           re.DOTALL):
        commands[cmd.group(1)] = cmd.group(2)
    return commands


if __name__ == '__main__':
    file_data = dict()
    for filename in os.listdir('./input'):
        data = open('./input/' + filename, 'r').read()
        fn = filename.replace('.txt', '')
        file_data[str(fn)] = data

    output = dict()
    for name, text in file_data.items():
        print(name)
        pattern = name + r'#\s*(.*?)\s*\n.*?(?=' + name + r'#)'
        for result in re.finditer(pattern, text, re.DOTALL):
            if name not in output.keys():
                output[name] = dict()
            output[name][exp_cmd(result.group(1))] = result.group(0).replace(' --More-- ', '').replace('\x08', '')

    for switch in output.keys():
        if 'show tech-support' in output[switch].keys():
            sh_tech_cmds = get_sh_tech_sub_commands(output[switch]['show tech-support'])
            for cmd, val in sh_tech_cmds.items():
                output[switch][cmd] = val
        for command in output[switch].keys():
            try:
                output[switch][command] = parse_output(platform="cisco_ios",
                                                       command=command,
                                                       data=output[switch][command])
            except:
                pass
                # output[switch][command] = output[switch][command]
            # if exp not in excluded_commands:
            #     if 'Invalid input detected' not in switches[switch][command]:
            #         output[switch][exp] = parse_output(platform="cisco_ios", command=exp, data=switches[switch][command])
            # else:
            #     output[switch][exp] = switches[switch][command]

    # Boilerplate code to copy switch sh tech output to paste into cisco CLI analyzer.
    # from xerox import copy, paste
    # for switch in output.keys():
    #     print(switch)
    #     try:
    #         copy(output[switch]['show tech-support'])
    #     except:
    #         print("There was an error.")
    #     input("Ready for the next switch?")

    # Boilerplate code to print a list of vlans on each of the switches.
    # a = [item for sublist in [output[x]['show vlan brief'] for x in output.keys()] for item in sublist]
    # vlans = list()
    # for x in a:
    #     vlans.append(x['vlan_id'])
    # vlans = [str(b) for b in sorted(list(set([int(c) for c in vlans])))]
    # for vlan in vlans:
    #     for x in a:
    #         if x['vlan_id'] == vlan:
    #             print(x)
    # Boilerplate code to write 'show interface' output to a csv file.
    # import csv
    #
    # with open('output.csv', 'w')  as output_file:
    #     dict_writer = csv.DictWriter(output_file, output[list(output.keys())[0]]['show interface'][0].keys())
    #     dict_writer.writeheader()
    #     for x in output.keys():
    #         dict_writer.writerows(output[x]['show interface'])

    output_csv = dict()
    for switch in output.keys():
        output_csv[switch] = dict()
        output_csv[switch]['interfaces'] = get_interface_vlans(output[switch]['show running-config'], 'ios')
        for interface in range(len(output_csv[switch]['interfaces'])):
            for mac in output[switch]['show mac address-table']:
                if output_csv[switch]['interfaces'][interface]['name'] == normalize_interface_names(
                        mac['destination_port']):
                    if 'mac_address-table' not in output_csv[switch]['interfaces'][interface].keys():
                        output_csv[switch]['interfaces'][interface]['mac_address-table'] = list()
                    output_csv[switch]['interfaces'][interface]['mac_address-table'].append(mac['destination_address'])
            output_csv[switch]['interfaces'][interface]['description'] = get_interface_description(
                output[switch]['show running-config'], 'ios', output_csv[switch]['interfaces'][interface]['name'])
            for interface_status in output[switch]['show interfaces status']:
                if interface_status['port'] == output_csv[switch]['interfaces'][interface]['name']:
                    output_csv[switch]['interfaces'][interface]['status'] = interface_status['status']
                    output_csv[switch]['interfaces'][interface]['speed'] = interface_status['speed']
                    output_csv[switch]['interfaces'][interface]['duplex'] = interface_status['duplex']
                    break
            for item_check in ['status', 'speed', 'duplex']:
                if item_check not in output_csv[switch]['interfaces'][interface].keys():
                    output_csv[switch]['interfaces'][interface][item_check] = ''
            if 'show cdp neighbor' in output[switch].keys():
                for neighbor in output[switch]['show cdp neighbor']:
                    if normalize_interface_names(neighbor['local_interface']) == normalize_interface_names(
                            output_csv[switch]['interfaces'][interface]['name']):
                        output_csv[switch]['interfaces'][interface]['neighbor'] = neighbor['neighbor'] + ' - ' + \
                                                                                  neighbor['platform'] + ' - ' + \
                                                                                  neighbor['neighbor_interface']

                        output_csv[switch]['interfaces'][interface]['mac_address-table'] = list()
            if 'neighbor' not in output_csv[switch]['interfaces'][interface].keys():
                output_csv[switch]['interfaces'][interface]['neighbor'] = ''
        output_csv[switch]['ipaddr'] = get_ip_from_sh_ip_int_br(output[switch]['show ip interface brief'])

    for switch_name, switch_data in output_csv.items():
        for interface in output_csv[switch_name]['interfaces']:
            if 'mac_address-table' not in interface.keys() or interface['mac_address-table'] == []:
                interface['mac_address-table'] = ['N/A']
            for mac in interface['mac_address-table']:
                print('\t'.join([switch_name,
                                 switch_data['ipaddr'],
                                 interface['name'],
                                 interface['mode'],
                                 interface['access-vlan'],
                                 ','.join(interface['trunk-vlans']),
                                 interface['native_vlan'],
                                 str(interface['tagged-native-vlan']),
                                 interface['description'],
                                 interface['status'],
                                 interface['speed'],
                                 interface['duplex'],
                                 interface['neighbor'],
                                 mac.replace('.', '').upper()]))

