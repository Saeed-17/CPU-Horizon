import subprocess
import os
import time

# 1) Function to list all cores which user has and to mention whether each core is performance or effeciency
def organize_cores():
    # print("Initialising variables...")
    thread_count = 0
    bin_toggle_vals = ""
    total_cores = 0
    core_files = ""
    # print("reading number or threads...")
    while(1):
        try:
            os.chdir(f'/sys/devices/system/cpu/cpu{thread_count}')
            thread_count += 1
        except:
            break
    # print("reading threads status...")
    for i in range(thread_count):
        try:
            bin_toggle_vals = f"{bin_toggle_vals}{open(f"/sys/devices/system/cpu/cpu{i}/online","r").read().replace("\n","")}"
        except:
            continue
    
    # print("enabling all threads...")
    for i in range(thread_count):
        try:
            open(f"/sys/devices/system/cpu/cpu{i}/online","w").write("1")
        except:
            continue
    # print("reading core data...")

    core_count = subprocess.getoutput("lscpu -e=CORE").replace("CORE","").replace(" ","").replace("\n","")
    
    temporary = ""
  
    #till here core count and thread count values are exactly what were directly taken as output of lscpu -e=(either CORE or CPU)
    cores = []
    i = 0
    #this loop will iterate over each character of the string, "core count" and accordingly store values in the variable "cores".
    #The values stored in cores will wither be P or E. If core_count contains 2 consecutive same numbers itll store a P because P cores hav 2 threads and E have only one thread.
    # print("organizing core data...")
    while i < (len(core_count)):
        
        temporary = core_count[i] 
        
        #above, temporary is just holding one character of core count and below, i will increase by 1 only if it doesnt cross the limits, tht is the reason for the if statement
        #temporary is required because once i changes, itll b looking at da next character n and we neeed to compare it to the previous one which is help by temporary
        if i < len(core_count) - 1 :
            i += 1
            
            if temporary == core_count[i]:
                

                    cores.append(f"{int(temporary) + 1}P")
                    with open(f"/usr/local/bin/{int(temporary) + 1}P","w") as f:
                        f.write(f"cpu{i-1},cpu{i}")
                    total_cores +=1
                
            else:
                
                    cores.append(f"{int(temporary)+1}E")
                    total_cores +=1
                    with open(f"/usr/local/bin/{int(temporary) + 1}E","w") as f:
                        f.write(f"cpu{i-1}")
                    try:
                        cores.append(f"{int(core_count[i]) + 1}E")
                        with open(f"/usr/local/bin/{int(core_count[i]) + 1}E","w") as f:
                            f.write(f"cpu{i}")
                        total_cores += 1
                    except:
                        pass

        i +=1
    
    # print("resetting to old thread status...")

    for i in range(thread_count):
        if i == 0:
            continue
        
        open(f"/sys/devices/system/cpu/cpu{i}/online","w").write(bin_toggle_vals[i-1])
        
    
    # print("reading and assigning status to organized cpu data...")

    
         

    for i in range(len(cores)):

        

        with open(f"/usr/local/bin/{cores[i]}","r") as f:
            core_files = f.read()

        core_files = core_files.replace("\n","").replace("online","").replace("offline","")
        if "," in core_files:
            
            temporary = ""
            j = 0
            while (core_files[j] != ","):
                temporary = f"{temporary}{core_files[j]}"
                j+=1
            
            core_files = core_files.replace(temporary,"").replace(",","")
        
        try:
            with open(f"/sys/devices/system/cpu/{core_files}/online","r") as f:
                 status = f.read()
        except:
            pass
        
        
        if "1" in status:
            with open(f"/usr/local/bin/{cores[i]}","a") as f:
                    f.write("\nOnline")
        else:
            with open(f"/usr/local/bin/{cores[i]}","a") as f:
                    f.write("\nOffline")
    temporary = ""
    # print("editing the list...")
    for i in range(len(cores)):
        with open(f"/usr/local/bin/{cores[i]}","r") as f:
              temporary = f.read()
        
        if "Offline" in temporary:
             
             cores[i] = f"{cores[i]}(Inactive)"
               
    return cores

# 2) Toggles cpu cores i.e it turns them on and off
def toggle_core(core):
    if core != "1P":
        contents = ""
        thread = ""
        thread_1 = ""
        status = 0
        try:
            with open(f"/usr/local/bin/{core}","r") as f:
                    contents = f.read()
            
            if "Online" in contents:
                    contents = contents.replace("Online","Offline")
                    status = 0

            elif "Offline" in contents:
                    contents = contents.replace("Offline","Online")
                    status = 1

            with open(f"/usr/local/bin/{core}","w") as f:
                    f.write(contents)
        except:
            print("Path error!")
        
        if contents != "" :
            contents = contents.replace("Online","").replace("\n","").replace("Offline","")
            if "," in contents:
                for i in range(len(contents)):
                    if contents[i] == ",":
                        break
                    else:
                        thread_1 = f"{thread_1}{contents[i]}"
                
                thread = contents.replace(thread_1,"").replace(",","")
                with open(f"/sys/devices/system/cpu/{thread}/online","w") as f:
                    f.write(f"{status}")
                with open(f"/sys/devices/system/cpu/{thread_1}/online","w") as f:
                    f.write(f"{status}")
            else:
                thread = contents
                with open(f"/sys/devices/system/cpu/{thread}/online","w") as f:
                    f.write(f"{status}")

def get_status():
    a = organize_cores()

    status = []

    for i in range(len(a)):
        if "(Inactive)" in a[i]:
            a[i] = a[i].replace("(Inactive)","").replace(" ","")
        try:
            with open(f"/usr/local/bin/{a[i]}","r") as f:
                    contents = f.read()

            if "Online" in contents:
                    status.append("Online")

            elif "Offline" in contents:
                    status.append("Offline")

        except:
            print(f"Path error!  --> {a[i]}")

    return status


# 3) Returns frequency of a pariular cpu core irrespective of single threaded or multi threaded
def freq_of(core):

    if core != "processor":

        thread0 = ""
        thread1 = ""
        frequency = 0
        frequency0 = 0
        try:

            # print("Opening core file...")

            with open(f"/usr/local/bin/{core}") as f:
                contents = f.read()


            # print("Editing variable contents...")


            contents = contents.replace("Offline","").replace("Online","").replace("\n","")

            # print("Moving to driver folders...")

            os.chdir("/sys/devices/system/cpu")

            if "," in contents:

                # print("Reading both the threads...")

                for i in range(len(contents)):
                     if contents[i] == ",":
                          break
                     else:
                          thread0 = f"{thread0}{contents[i]}"

                # print("Organising thread data...")


                thread1 = contents.replace(thread0,"").replace(",","")


                # print("Reading thread0 frequency...")

                with open(f"{thread0}/cpufreq/scaling_cur_freq","r") as f:
                    frequency = int(f.read())


                # print("Reading, adding and averaging to thread1 freq...")



                with open(f"{thread1}/cpufreq/scaling_cur_freq","r") as f:
                    frequency0 = int(f.read())

                frequency = float((frequency+frequency0)/2)

                # print("done...")

            else:
                 thread0 = contents

                #  print("Reading core driver folder...")

                 with open(f"{thread0}/cpufreq/scaling_cur_freq","r") as f:
                    frequency = int(f.read())

                #  print("Done...")



            return round(frequency/1000000,1)


        except:
             return 0

    elif core == "processor":
        frequency = 0.0
        divider = 0
        for i in range(len(organize_cores())):
            if organize_cores()[i] != 0:
                divider += 1
                frequency += freq_of(organize_cores()[i])

        frequency = round((frequency/ divider),2)
        return f"{frequency}"

# 4) Returns name of cpu
def cpu_name():
    a = subprocess.getoutput('lscpu | grep "Model name"')
    b = ""
    for i in range(len(a)):
         if a[i] == "\n":
              break
         else:
              b += a[i]

    return b.replace("Model name:","").replace("                              ","")

# 5) Returns type of cpu
def type():
    a = organize_cores()
    type = ""
    for i in range(len(a)):
        if "P" in a[i] and "P" not in type:
            type += "P"
        elif "E" in a[i] and "E" not in type:
            type += "E"

    if "P" in type and "E" in type:
        type = "hybrid"
    else:
        type = "non-hybrid"
    
    return type

# 6) sets min cpu percentage
def set_min_freq(percentage):

    print("checking percentage validity...")

    if percentage > 100 or percentage < 0:
        return "invalid percentage"
    else:

        print("Initialising ...")

        i = 0
        min_capacity = ""
        max_capacity = ""
        min_freq = ""
        
        while 1:
            a = 0
            try:

                print(f"reading min capacity of thread {i}...")

                with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/cpuinfo_min_freq","r") as f:
                    min_capacity = f.read().replace("\n","")

                print(f"reading max capacity of thread {i}...")

                with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/cpuinfo_max_freq","r") as f:
                    max_capacity = f.read().replace("\n","")

                print("manipulating values...")

                min_capacity = int(min_capacity)
                max_capacity = int(max_capacity)
                a = max_capacity - min_capacity

                print(f"minimum capacity for thread is {min_capacity}")

                a = int(a*(percentage/100))

                print(f"increasing by {a}")

                min_freq = int(a + int(min_capacity))

                print(f"manipulated frequency is {min_freq}")

                if min_freq >= min_capacity and min_freq <= max_capacity:

                    print("writing values...")
                    with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_min_freq","w") as f:
                        f.write(f"{min_freq}")

                    i += 1

            except: 
                print("thread not found... ")
                break

# 7) View min cpu frequency:
def check_min_freq():
 
    i = 0
    capacity = ""
    freq = 0
    while 1:
        try:
            with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_min_freq","r") as f:
                capacity = f.read().replace("\n","")
                i += 1
            freq += int(capacity)
        except:
            break
    return round((freq/i)/1000000,2)

# 8) sets max cpu percentage (DO THIS VERRRY VERRRRY IMPORTANT)
def set_max_freq(percentage):

    print("checking percentage validity...")

    if percentage > 100 or percentage < 0:
        return "invalid percentage"
    else:

        print("Initialising ...")

        i = 0
        min_capacity = ""
        max_capacity = ""
        max_freq = ""
        cur_min_freq = ""
        
        while 1:
            a = 0
            try:

                print(f"reading min capacity of thread {i}...")

                with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/cpuinfo_min_freq","r") as f:
                    min_capacity = f.read().replace("\n","")

                print(f"reading max capacity of thread {i}...")

                with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/cpuinfo_max_freq","r") as f:
                    max_capacity = f.read().replace("\n","")

                print("manipulating values...")

                min_capacity = int(min_capacity)
                max_capacity = int(max_capacity)
                a = max_capacity - min_capacity

                print(f"minimum capacity for thread is {min_capacity}")

                a = int(a*(percentage/100))

                print(f"increasing by {a}")

                max_freq = int(a + int(min_capacity))

                print(f"manipulated frequency is {max_freq}")

                with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_min_freq","r") as f:
                    cur_min_freq = f.read()

                if max_freq >= min_capacity and max_freq <= max_capacity and max_freq >= int(cur_min_freq):

                    print("writing values...")
                    with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_max_freq","w") as f:
                        f.write(f"{max_freq}")

                    i += 1

            except: 
                print("thread not found... ")
                break

# 9) View max cpu frequency:
def check_max_freq():
 
    i = 0
    capacity = ""
    freq = 0
    while 1:
        try:
            with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_max_freq","r") as f:
                capacity = f.read().replace("\n","")
                i += 1
            freq += int(capacity)
        except:
            break
    return round((freq/i)/1000000,2)

# 10) Set cpu power limits STILL LEFT TO DO
def setPL(pl1):
    limit1 = 0
    limit = 0
    pl2 = (pl1 + 5)

    if pl1 < 10:
        pl2 += 5

    pl2 = pl2*1000000

    pl1 = pl1*1000000
    with open("/sys/class/powercap/intel-rapl:0/constraint_0_max_power_uw","r") as f:
        limit = int(f.read())

    with open("/sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw","w") as f:
        f.write(f"{pl1}")

    with open("/sys/class/powercap/intel-rapl:0/constraint_1_power_limit_uw","w") as f:
        f.write(f"{pl2}")

    with open("/sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw","r") as f:
        limit1 = int(f.read())

    if limit1 > limit:
        with open("/sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw","w") as f:
            f.write(str(limit))
        limit1 = limit

    return f"{limit1/1000000} W"

def show_power1():
    with open("/sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw","r") as f:
        limit1 = int(f.read())
    return limit1/1000000

def show_power2():
    with open("/sys/class/powercap/intel-rapl:0/constraint_1_power_limit_uw","r") as f:
        limit1 = int(f.read())
    return limit1/1000000

def power_capacity():
    with open("/sys/class/powercap/intel-rapl:0/constraint_0_max_power_uw","r") as f:
        limit = int(f.read())
    return int(limit)/1000000


def cores_usage(percentage):
    cores = organize_cores()
    total_cores = int((percentage/100)*len(cores))
    
    new_cores = ['1']

    for i in range(total_cores):
        new_cores.append('0')

    while len(cores) > len(new_cores):
        new_cores.append('1')

    return new_cores
