import datetime
import playsound
import threading
import time
import MainJarvis_TaskExecution
from MainJarvis_TaskExecution import speak

def alarm(Timing):
    try:
        # Ensure proper formatting by stripping extra spaces
        Timing = Timing.strip()

        # Convert given time string to datetime object
        altime = datetime.datetime.strptime(Timing, "%I:%M %p")

        Horeal = altime.hour
        Mireal = altime.minute

        speak(f"Done, alarm is set for {Timing}")

        while True:
            now = datetime.datetime.now()
            if Horeal == now.hour and Mireal == now.minute:
                print("TIMES UP")
                print("Alarm will RUN now")
                playsound.playsound(r"C:\Users\Omkar Raut\OneDrive\Desktop\PYTHON\JARVIS\alarm.wav")
                break  # Stop the loop after playing the alarm sound
            time.sleep(1)  # Check every second to avoid excessive CPU usage

    except Exception as e:
        MainJarvis_TaskExecution.speak(f"Sorry Sir.Error in setting alarm. Please try again later.")
        print(e)

# Function to start alarm in a separate thread to prevent blocking
def start_alarm(Timing):
    alarm_thread = threading.Thread(target=alarm, args=(Timing,))
    alarm_thread.start()
