import threading
import time
import sys
from internet_check import is_Online
from Alert import Alert
from Data.DLG_Data import online_dlg,offline_dlg
import random
from co_brain import Jarvis
from TextToSpeech.Fast_DF_TTS import speak
from Automation.Battery  import check_plug
from Time_Operations.throw_alert import check_schedule,check_Alam
from os import getcwd

Alam_path = f"{getcwd()}\\Alam_data.txt"
file_path = f'{getcwd()}\\schedule.txt'

ran_online_dlg = random.choice(online_dlg)
ran_offline_dlg = random.choice(offline_dlg)


def main():
    if is_Online():
        t1 = threading.Thread(target=speak, args=(ran_online_dlg,), daemon=True)
        t3 = threading.Thread(target=check_plug, daemon=True)
        t4 = threading.Thread(target=check_schedule, args=(file_path,), daemon=True)
        t5 = threading.Thread(target=Jarvis, daemon=True)
        t6 = threading.Thread(target=check_Alam, args=(Alam_path,), daemon=True)
        t1.start()
        t1.join()
        t3.start()
        t4.start()
        t5.start()
        t6.start()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[!] Jarvis stopping...")
            sys.exit(0)
    else:
        Alert(ran_offline_dlg)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Jarvis stopping...")
        sys.exit(0)