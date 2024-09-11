import argparse
import os
import geocoder
import folium
from ping3 import ping
from prettytable import PrettyTable
import re

print(r"""                                                                                                        
      
    Please note this tool is for educational purposes
                                                                                    
""")

def pingIP(ip):
    try:
        pingTime = ping(ip)
        if pingTime is not None:
            print("IP [", ip, "] Is active")
            return "Active"
        else:
            print("IP [", ip, "] Is NOT active")
            return "Not Active"            
    except Exception as e:
        print("Error:", e)
        print("Error while pinging")
        return "Not Active"

def NmapStage(ip):
    nmapcommand = "sudo nmap -sT -O " + ip + "> output.txt"
    os.system(nmapcommand)

    resultNew = "cat output.txt |grep 'open'|sed 's/open//g'|sed 's/\/tcp//g'|sed -e 's/\s\+/,/g' > openports.txt"
    os.system(resultNew)
    results2 = "cat output.txt | grep 'OS details' | cut --complement -b 1-12 > os_guess.txt"
    os.system(results2)

    with open('os_guess.txt') as f:
        osguess = f.read()

    with open('openports.txt') as f:
        open_ports = f.readlines()

    table = PrettyTable(["Port Number", "Description"])
    for line in open_ports:
        line = line.strip()
        currentline = line.split(",")
        portnumber = currentline[0]
        portdescription = currentline[1]
        table.add_row([portnumber, portdescription])

    with open('REPORT.txt', 'w') as report_file:
        report_file.write("Footprinting results:\n")
        report_file.write("The operating system was guessed as " + osguess + "\n")
        report_file.write("Open Ports:\n")
        report_file.write(str(table))

    try:
        html_file_path = ip_local()
        if html_file_path:
            print("Map successfully created")
            with open('REPORT.txt', 'a') as report_file:
                report_file.write("\nHTML Report: HTML map successfully created. See files for HTML file.\n")
        else:
            print("Map NOT created")
            with open('REPORT.txt', 'a') as report_file:
                report_file.write("\nHTML Report: HTML map NOT created.\n")
    except Exception as x:
        print("Error:", x)
        print("Another issue has occurred")
        with open('REPORT.txt', 'a') as report_file:
            report_file.write("\nHTML Report: Error occurred while creating HTML map.\n")

    add_divider_to_report()
    perform_nikto_scan(ip)
    add_divider_to_report()
    search_CVEs()
    add_divider_to_report()
    perform_dirb_scan(ip)
    add_divider_to_report()
    perform_wp_scan()

def ip_local():
    try:
        target = geocoder.ip(ip)
        myaddress = target.latlng
        target_location = folium.Map(location=myaddress, zoom_start=12)
        folium.Marker(myaddress, popup="Target")
        target_location.save("Target_Location.html")
        return "Target_Location.html"
    except Exception as e:
        print("Error:", e)
        print("Error: Image locator can't work on a private IP")
        return None

def perform_nikto_scan(ip):
    if not os.path.exists('openports.txt'):
        print("Open ports file not found.")
        return

    with open('openports.txt', 'r') as f:
        open_ports = f.readlines()

    found = False
    
    for entry in open_ports:
        port_number, _ = entry.split(',')
        if port_number.strip() in ['80', '443']:
            found = True
            print("Port 80 or 443 found")
            nikto_command = f"nikto -host {ip} >> nikto_scan.txt"
            os.system(nikto_command)

            with open('nikto_scan.txt', 'r') as f:
                nikto_results = f.read()

            with open('REPORT.txt', 'a') as report_file:
                report_file.write("\nNikto Scan Results:\n")
                report_file.write(nikto_results)
            
            print("Nikto scan completed and results added to the report.")
            break
    
    if not found:
        print("Neither port 80 nor 443 found. Skipping Nikto scan.")

def add_divider_to_report():
    try:
        with open('REPORT.txt', 'a') as report_file:
            report_file.write("\n" + "=" * 50 + "\n")
    except Exception as e:
        print("Error:", e)

def perform_dirb_scan(ip):
    if not os.path.exists('openports.txt'):
        print("Open ports file not found.")
        return

    with open('openports.txt', 'r') as f:
        open_ports = f.readlines()

    found = False
    
    for entry in open_ports:
        port_number, _ = entry.split(',')
        if port_number.strip() in ['80', '443']:
            found = True
            print("Port 80 or 443 found")
            dirb_command = f"dirb http://{ip} > dirb_scan.txt"
            os.system(dirb_command)

            print("Dirb scan completed.")

            break
    
    if not found:
        print("Neither port 80 nor 443 found. Skipping Dirb scan.")

def perform_wp_scan():
    # Open dirb scan results
    with open('dirb_scan.txt', 'r') as f:
        dirb_results = f.readlines()
        # Filter for WordPress directories
        wp_directories = [line.split()[-1] for line in dirb_results if line.startswith('==> DIRECTORY')]
            
        if wp_directories:
            print("WordPress directories found:", wp_directories)
            for directory in wp_directories:
                wpscan_command = f"wpscan --url {directory} > wpresults.txt"
                os.system(wpscan_command)
                print(wpscan_command)

                # Check if the scan was aborted
                with open('wpresults.txt', 'r') as wpscan_file:
                    wpresults = wpscan_file.read()
                    with open('REPORT.txt', 'a') as report_file:
                        if "Scan Aborted: The remote website is up, but does not seem to be running WordPress." in wpresults:
                            report_file.write(f"\nWPScan Results for {directory}:\n")
                            report_file.write("Not running WordPress here\n")
                        else:
                            report_file.write(f"\nWPScan Results for {directory}:\n")
                            report_file.write(wpresults)

        else:
            print("No WordPress directories found. Skipping WPScan.")



def search_CVEs():
    with open('REPORT.txt', 'r') as report_file:
        report_content = report_file.read()

    # Use regular expression to find CVEs
    cve_pattern = r'CVE-\d{4}-\d{4,7}'
    cve_matches = re.findall(cve_pattern, report_content)

    # Remove duplicates
    cve_matches = list(set(cve_matches))

    with open('REPORT.txt', 'a') as report_file:
        report_file.write("\nCVE Search Results:\n")

        for cve in cve_matches:
            report_file.write(f"\nSearching for CVE: {cve} Please note that searchsploit might not find the current exploit please check here: https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword={cve}\n")
            searchsploit_command = f"searchsploit {cve}"
            search_result = os.popen(searchsploit_command).read()
            report_file.write(search_result)

            # Print the CVE found to the terminal
            print(f"Found CVE: {cve}")

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
req_args = parser.add_argument_group('required arguments')
req_args.add_argument("IP", help="The target IP, example: 192.168.0.1")
args = parser.parse_args()
ip = str(args.IP)
print("The IP specified was", ip)

pingresults = pingIP(ip)

if pingresults == "Active":
    NmapStage(ip)
else:
    print("Enter a valid IP")

