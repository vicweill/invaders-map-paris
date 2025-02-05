# Après avoir exporté les données d'Invader Spotter,
# on pourra générer les images de chaque SI

import os
import pandas as pd
from tqdm import tqdm

from utils.extract_functions import generate_image_url, download_png


df = pd.read_csv("data/invader_spotter_art_listing.csv")

df_with_url = generate_image_url(df)

# List of URLs to download
urls = df_with_url['url'].tolist()

# Create the directory to save images if it doesn't exist
save_dir = "img/"
os.makedirs(save_dir, exist_ok=True)

# Loop over the list of URLs and download each PNG file
for url in tqdm(urls, desc="Téléchargement des images", unit="image"):
    download_png(url, save_dir)
