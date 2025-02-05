# Code de scraping des données d'Invader Spotter
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

from utils.extract_functions import *

# Specify the path to the web page
path = "https://www.invader-spotter.art/cherche.php"

# Initialize the WebDriver
print(" > Starting the Chrome driver...")
driver = get_headless_driver()

print(" > Let's extract data from Invader Spotter :")
df = scraping_invader_spotter(driver, path, nb_pages=32)

# Extract data into clean column names
df['name'] = df[1].apply(extract_name)
df['dispointstrict'] = df[1].apply(extract_points)
df['district'] = df[3].apply(extract_district)
df['state'] = df[4].apply(extract_state)

# Keep a trace of the extraction date
extraction_date = datetime.today().strftime('%Y-%m-%d')
df['extraction_date'] = extraction_date

df = df.sort_values('name')

df.to_csv("data/invader_spotter_art_listing.csv")

print(" > Extracted : ", str(len(df)), " invaders from Invader Spotter !")

driver.quit()

print(" > Driver exited successfully")

# Part 2 : Download images

df_with_url = generate_image_url(df)

# List of URLs to download
urls = df_with_url['url'].tolist()

# Create the directory to save images if it doesn't exist
save_dir = "img/"
os.makedirs(save_dir, exist_ok=True)

# Loop over the list of URLs and download each PNG file
for url in tqdm(urls, desc="Téléchargement des images", unit="image"):
    download_png(url, save_dir)
