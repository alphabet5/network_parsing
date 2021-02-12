# network_parsing
 Script to parse raw network output from putty.

## Requirements

- python3 (3.9)
- ntc-templates

## Usage

For parse_outputs.py

- Create an input directory at ./input
- Place individual files for each switch from running `sh tech` and `sh mac address-table`
- Run the file. This will output with the standard structure from alphabet5/cisco_documentation

For eip_parse.py

- Place the output from nmaps enip-info scan into ./eip-info.txt
- Run the file. This will output structured data from the nmap command including ip, type, and product name.