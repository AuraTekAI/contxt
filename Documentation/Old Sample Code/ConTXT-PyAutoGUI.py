import subprocess
import pyautogui
import time
import tkinter as tk
from tkinter import messagebox
import random

def random_delay(minimum=0.5, maximum=1.5):
    return random.uniform(minimum, maximum)

# Open Firefox
subprocess.Popen(["C:\\Program Files\\Mozilla Firefox\\firefox.exe"])
time.sleep(5)  # Wait for Firefox to open

# Maximize the window
pyautogui.hotkey('win', 'up')  # Maximize window
time.sleep(5)  # Wait for the CorrLinks login page to load

# Navigate to the login button using tab keys
for _ in range(3):  # Adjust the number based on how many tabs are needed
    pyautogui.press('tab')
    time.sleep(random_delay(0.2, 0.5))

# Press enter to click the login button
pyautogui.press('enter')
time.sleep(random_delay(0.5, 1.0))
time.sleep(random_delay(0.5, 1.0))
time.sleep(random_delay(0.5, 1.0))

# Navigate to the inbox
pyautogui.hotkey('ctrl', 'l')  # Focus the address bar
time.sleep(random_delay(0.5, 1.0))
pyautogui.write('https://www.corrlinks.com/Inbox.aspx?UnreadMessages')
pyautogui.press('enter')
time.sleep(5)  # Wait for the inbox page to load