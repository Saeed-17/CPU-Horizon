# CPU Horizon (HZN)

A simple Linux tool to control CPU cores and monitor per-core behavior.

## Features

- Toggle CPU cores
- View per core frequency
- Check core status
- View Power limits

## Why i made this?
I wanted more control over thermals and battery on my laptop.
Disabling some cores dropped temps by ~8–10°C in my testing.

## Example Usage

This shows all of my cpu cores on the left side(not threads). On the right side is the frequency load and the power limits of the cpu.
<img width="899" height="680" alt="image" src="https://github.com/user-attachments/assets/8c7df94d-0dad-4487-bcf6-9969387e915b" />
I can basically monitor the frequency of each cpu core and its status. 
I can turn cpu cores on/off as well by clicking the cpu cores(it might take 1 - 1.5 seconds):
<img width="899" height="681" alt="image" src="https://github.com/user-attachments/assets/1722f1a7-9b67-4e0d-9ab3-2d44e20a9741" />
This has successfully toggled those cpu cores. You can confirm and monitor if it actually happens by either checking in a system monitor application if available or by doing:
```bash
lscpu -e
```
In my case it has successfully toggled:
<img width="1149" height="444" alt="image" src="https://github.com/user-attachments/assets/5534807b-0ca2-4650-914d-e961b8958654" />

## Safety
- no background processes will run
- no usage of netwrok
- turning off all cores is impossible(turning off the first cpu core is not possible, it wont happenning even if you try clicking it). This prevents kernel panic.

## Installation
```bash
git clone https://github.com/Saeed-17/CPU-Horizon
chmod +x HZN
sudo ./HZN



