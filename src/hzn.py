import cpu
import monitor_ui
import threading
import time
from PySide6.QtCore import QTimer

cores = cpu.organize_cores()

def get_frequencies():
    frequencies = []
    for i in range(len(cores)):
        try:
            frequencies.append(f"{str(cpu.freq_of(cores[i]))} GHz")
        except:
            pass
    return frequencies

def get_freq():
    total = 0
    for i in range(len(cores)):
        try:
            total += cpu.freq_of(cores[i])
            # print(f"total: {total} freq: {cpu.freq_of(cores[i])}")
        except:
            pass
    min_freq = cpu.check_min_freq()
    max_range = cpu.check_max_freq() - min_freq
    # print(f"min is {min_freq}")
    total /= len(cores) - min_freq
    # print(f"Average is {total}")
    # print(f"max is {cpu.check_max_freq()}")
    return round((total / max_range)*100,1)

def on_core_click(index: int):
    core = cores[index]

    if "(Inactive)" in core:
        core = core.replace("(Inactive)","").replace(" ","")
    cpu.toggle_core(core)




monitor_ui.sectionA(cpu.cpu_name())
monitor_ui.sectionB(len(cores), cpu.get_status(), get_frequencies(), on_click=on_core_click)
monitor_ui.sectionC(get_freq(), cpu.show_power1(), cpu.show_power2())



def update():
    monitor_ui.sectionB(len(cores), cpu.get_status(), get_frequencies(), on_click=on_core_click)
    monitor_ui.sectionC(get_freq(), cpu.show_power1(), cpu.show_power2())

timer = QTimer()
timer.timeout.connect(update)
timer.start(1000)

monitor_ui.run()

