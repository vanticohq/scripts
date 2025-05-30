#!/bin/bash

# Check if input file is provided

if [ "$#" -ne 2 ]; then

echo "Usage: $0 <input_nmap_file> <output_csv_file>"

exit 1

fi

# Input and Output files

input_file=$1

output_file=$2

# Check if the input Nmap file exists

if [ ! -f "$input_file" ]; then

echo "Error: Input file does not exist."

exit 1

fi

# Create the CSV file and add the header

echo "host,port,state,service" > "$output_file"

 

# Parse the Nmap file

host=""

while IFS= read -r line; do

# Check if line starts with "Nmap scan report for" (indicating a new host)

if [[ $line =~ ^Nmap\ scan\ report\ for\ (.*) ]]; then

     host="${BASH_REMATCH[1]}"

     echo "Found host: $host"  # Debugging: print host when found

fi

# Check if line contains port info (TCP/UDP ports)

# Adjust the regex to ensure matching is more flexible with spaces and tabs

if [[ $line =~ ([0-9]+)/(tcp|udp)[[:space:]]+(open|closed)[[:space:]]+([a-zA-Z0-9\-]+) ]]; then

     port="${BASH_REMATCH[1]}"

     protocol="${BASH_REMATCH[2]}"

     state="${BASH_REMATCH[3]}"

     service="${BASH_REMATCH[4]}" 

     # Debugging: print port, state, service

     echo "Found port: $port/$protocol, state: $state, service: $service"

     # Write the host, port, state, and service to the CSV file

     echo "$host,$port/$protocol,$state,$service" >> "$output_file"

fi

done < "$input_file"

echo "CSV file created at $output_file"
