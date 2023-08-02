import re
import os
from datetime import datetime
from netmiko import ConnectHandler
import shutil

Ipfilter = re.compile(r"\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
Hostfilter = re.compile(r"hostname (\S+)")
Iosxe = re.compile(r"\bIOS[- ]XE")
Iosxr = re.compile(r"\bIOS[- ]XR")


USERNAME = os.environ.get("USER")
PASSWORD = os.environ.get("PASS")





class GetConfig:
    def __init__(self):

        self.currentpath = os.getcwd()
        self.cfg_dir_path = os.path.join(self.currentpath, "IOSx_Config_Files_All")
        self.cfg_dir_log = os.path.join(self.cfg_dir_path, "logs")
        self.cfg_dir_last = os.path.join(self.cfg_dir_path, "all_configs_de")
        self.cfg_dir_site = os.path.join(self.cfg_dir_path, "de")
        self.cfg_dir_site_rt= os.path.join(self.cfg_dir_site, "routers")
        self.cfg_dir_site_sw = os.path.join(self.cfg_dir_site, "switches")
        self.cfg_dir_site_rt_vend = os.path.join(self.cfg_dir_site_rt,"cisco")
        self.cfg_dir_site_sw_vend = os.path.join(self.cfg_dir_site_sw, "cisco")
        self.cfg_dir_site_rt_vend_ios = os.path.join(self.cfg_dir_site_rt_vend,"ios")
        self.cfg_dir_site_rt_vend_ios_xe = os.path.join(self.cfg_dir_site_rt_vend, "ios_xe")
        self.cfg_dir_site_rt_vend_ios_xr = os.path.join(self.cfg_dir_site_rt_vend, "ios_xr")
        self.cfg_dir_site_sw_vend_ios = os.path.join(self.cfg_dir_site_sw_vend,"ios")
        self.cfg_dir_site_sw_vend_ios_xe = os.path.join(self.cfg_dir_site_sw_vend, "ios_xe")
        self.source_dict = dict()
        self.source_dict["cisco_ios"] = "device_ips_ios_iosxe.txt"
        self.source_dict["cisco_xr"] = "device_ips_iosxr.txt"
        today = datetime.now().date()
        logfile_name = str(today) + "_log.txt"
        self.logfile = os.path.join(self.cfg_dir_log, logfile_name)
        self.validated_ips_list = []
        self.create_homepath()
        self.validate_source_files()


    def create_homepath(self):
        if  os.path.isdir(self.cfg_dir_path) is False:
            os.mkdir(self.cfg_dir_path)
            os.mkdir(self.cfg_dir_log)
            print()
            print("config folder: ./IOSx_Config_Files_DE created")
            print("create subfolders...")
            print()

        else:
            pass

        if os.path.isdir(self.cfg_dir_last):
            print()
            print("cleanup folder: " + "./"+ os.path.basename(self.cfg_dir_path)+ "/" + os.path.basename(self.cfg_dir_last))
            shutil.rmtree(self.cfg_dir_last)

        if os.path.isdir(self.cfg_dir_site):
            print("cleanup folder: " + "./"+ os.path.basename(self.cfg_dir_path)+ "/" + os.path.basename(self.cfg_dir_site))
            shutil.rmtree(self.cfg_dir_site)
            print()

        if not os.path.isdir(self.cfg_dir_log):
            os.mkdir(self.cfg_dir_log)
            print("created log folder: " + os.path.basename(self.cfg_dir_log))

        os.mkdir(self.cfg_dir_last)
        os.mkdir(self.cfg_dir_site)
        os.mkdir(self.cfg_dir_site_rt)
        os.mkdir(self.cfg_dir_site_sw)
        os.mkdir(self.cfg_dir_site_rt_vend)
        os.mkdir(self.cfg_dir_site_sw_vend)
        os.mkdir(self.cfg_dir_site_rt_vend_ios)
        os.mkdir(self.cfg_dir_site_rt_vend_ios_xe)
        os.mkdir(self.cfg_dir_site_rt_vend_ios_xr)
        os.mkdir(self.cfg_dir_site_sw_vend_ios)
        os.mkdir(self.cfg_dir_site_sw_vend_ios_xe)

        
    def validate_source_files(self):
        device_type_ips = dict()
        validated_ips_list_unmatched =[]

        for device_type, file_name in self.source_dict.items():
            self.source_ip_file = os.path.join(self.currentpath, file_name)



            if os.path.isfile(self.source_ip_file):
                with open(self.source_ip_file, "r") as file:
                    file_get = file.read()
                    ip = Ipfilter.findall(file_get)
                    validated_ips_list_unmatched.extend(ip)


                if validated_ips_list_unmatched ==[]:
                    print()
                    print("no entry in device file " + file_name + " found")
                    validated_ips_list_unmatched = []


                else:
                    device_type_ips[device_type] = validated_ips_list_unmatched
                    validated_ips_list_unmatched = []

                    validated_ips_list =[]
                    for unmatched_ip in device_type_ips[device_type]:

                          splitted_ip = unmatched_ip.split(".")
                          oktetts = [re.sub(r'\b0+(\d)', r'\1', oktett) for oktett in splitted_ip]
                          ip_checked = ".".join(oktetts)

                          validated_ips_list.append(ip_checked)

                    device_type_ips[device_type] = validated_ips_list


            else:
                print("file " + file_name +" missing")
                print("creating file...")
                print()
                with open(self.source_ip_file, "w") as newfile:
                    val = "*** please add management ip's of "+ device_type + "  devices below; one ip per line ***"
                    newfile.write(val)

        self.gather_configs(device_type_ips)

    def gather_configs(self,device_type_ips):




        for cisco_type in device_type_ips:
            print()
            print("try to gather running-config from " + str(len(device_type_ips[cisco_type])) + " " + cisco_type + " devices")
            print()
            for ip in device_type_ips[cisco_type]:


                try:
                   print("trying " + ip)
                   net_connect = ConnectHandler( device_type=cisco_type,
                                                host=ip,
                                                username=USERNAME,
                                                password=PASSWORD)



                   self.version = net_connect.send_command("show version")
                   self.config = net_connect.send_command("show run all")

                   self.hostname = re.findall(Hostfilter,self.config)[0].lower()


                   print("ok")


                   self.check_device_type(ip)

                except Exception as expt:
                  res = str(expt)
                  error_code = res.split("\n")[0]
                  print(error_code)
                  now = datetime.now()
                  now_format = now.strftime("%Y-%m-%d %H:%M:%S")
                  with open(self.logfile, "a") as lgfile:
                    logline = ("{:20} : {:3}{:15} : {:15s}\n".format(now_format, "ip=",ip,  error_code))

                    lgfile.write(logline)


        print()
        print("Done.")
        print()

    def check_device_type(self,ip):
        if re.search(Iosxe, self.version) and ("router bgp" in self.config or "router ospf" in self.config):
            # IOS XE Router
            filename = os.path.join(self.cfg_dir_site_rt_vend_ios_xe, self.hostname + ".cfg")
        elif re.search(Iosxe, self.version):
            #  IOS XE Switch
            filename = os.path.join(self.cfg_dir_site_sw_vend_ios_xe, self.hostname + ".cfg")
        elif re.search(Iosxr, self.version):
            # IOS XR Router
            filename = os.path.join(self.cfg_dir_site_rt_vend_ios_xr, self.hostname + ".cfg")
        elif "router bgp " in self.config or "router ospf " in self.config:

            # IOS Router
            filename = os.path.join(self.cfg_dir_site_rt_vend_ios, self.hostname + ".cfg")
        else:
            # IOS Switch
            filename = os.path.join(self.cfg_dir_site_sw_vend_ios, self.hostname + ".cfg")
       
        self.save_config(filename, ip)
        
        

    def save_config(self, filename, ip):
        filename_ip = os.path.join(self.cfg_dir_last, self.hostname + "_" + ip + ".cfg")
        with open(filename, "w") as savefiledir:
            savefiledir.write(self.config)
        with open(filename_ip, "w") as savefilelatest:
            savefilelatest.write(self.config)
        with open(self.logfile, "a") as lgfile:
            now = datetime.now()
            now_format = now.strftime("%Y-%m-%d %H:%M:%S")
            logline = ("{:20} : {:3}{:15} : {:15s}\n".format(now_format, "ip=", ip, "ok"))
            lgfile.write(logline)





if __name__ == "__main__":
    GetConfig()



