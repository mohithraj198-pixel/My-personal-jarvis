from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from os import getcwd
import time
from TextToSpeech.Fast_DF_TTS import is_speaking

# Setting up Chrome options with specific arguments
chrome_options = Options()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--headless=new")  # Modern headless mode
# Use Selenium Manager to automatically handle chromedriver matching the installed Chrome version
service = Service()
# Setting up the Chrome driver with the service and options
driver = webdriver.Chrome(service=service, options=chrome_options)
# Creating the URL for the website using the current working directory
website = "https://allorizenproject1.netlify.app/"
# Opening the website in the Chrome browser
driver.get(website)
Recog_File = f"{getcwd()}\\input.txt"

def listen():
    try:
        start_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'startButton')))
        start_button.click()
        print("Listening...")
        output_text = ""
        last_submitted_text = ""
        last_submitted_time = 0.0

        while True:
            try:
                output_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'output')))
                current_text = output_element.text.strip()
            except Exception:
                time.sleep(0.05)
                continue

            # Auto-restart speech recognition if it pauses
            try:
                if "Start Listening" in start_button.text and not is_speaking():
                    start_button.click()
                    time.sleep(0.2)
            except Exception:
                pass

            # 1. If Jarvis is speaking (or in echo grace period), mark current speech as seen and discard
            if is_speaking():
                output_text = current_text
                time.sleep(0.05)
                continue

            # 2. When new speech arrives:
            if current_text != output_text:
                if current_text.startswith(output_text):
                    new_part = current_text[len(output_text):].strip()
                else:
                    new_part = current_text
                output_text = current_text

                if not new_part:
                    time.sleep(0.05)
                    continue

                now = time.time()
                # Deduplicate identical recognition within 2.0s
                if new_part.lower() == last_submitted_text.lower() and (now - last_submitted_time) < 2.0:
                    time.sleep(0.05)
                    continue

                last_submitted_text = new_part
                last_submitted_time = now

                with open(Recog_File, "w", encoding="utf-8") as file:
                    file.write(new_part.lower())
                print("User:", new_part)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Process interrupted by user.")
    except Exception as e:
        print("An error occurred:", e)
    finally:
        driver.quit()