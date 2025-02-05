from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pandas as pd
import re
import os
import requests
import time
from tqdm import tqdm


def extract_rows(driver):
    # Get the content of the first <table> tag
    table = driver.find_element(By.TAG_NAME, 'table')

    # Extract rows and columns
    rows = table.find_elements(By.CSS_SELECTOR, 'tr.haut')
    data = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        row_data = []
        for col in cols:
            # Split the text by <br> tags
            cell_data = col.get_attribute('innerHTML').split('<br>')
            cell_data = [field.strip() for field in cell_data if field.strip()]  # Strip whitespace and remove empty fields
            row_data.extend(cell_data)
        data.append(row_data)

    # Convert to Pandas DataFrame
    df = pd.DataFrame(data)
    return(df)


def scraping_invader_spotter(driver, path, nb_pages=32):
    """
    Scrape les données de Invader Spotter.

    Args:
        driver (webdriver): Le driver Selenium.
        path (str): L'URL de la page à scraper.
        nb_pages (int, optional): Nombre total de pages à scraper (défaut: 32).

    Returns:
        pd.DataFrame: Un DataFrame contenant toutes les données extraites.
    """
    # Ouvrir la page en mode headless
    driver.get(path)

    # Sélectionner Paris
    driver.find_element(By.ID, "lieutoutparis").click()
    driver.find_element(By.ID, "toutparis").click()

    # Clic sur le bouton de recherche (dernier <p>)
    all_paragraphs = driver.find_elements(By.TAG_NAME, "p")
    last_paragraph = all_paragraphs[-1]
    image_button = last_paragraph.find_element(By.TAG_NAME, "input")
    image_button.click()

    # Boucle sur toutes les pages avec tqdm pour voir l'avancement
    res = []
    for page in tqdm(range(1, nb_pages + 1), desc="Scraping des pages", unit="page"):
        # Exécuter JavaScript pour changer de page
        driver.execute_script(f"javascript:changepage({page})")

        # Attendre que la page se charge (on suppose qu'un <table> est présent sur chaque page)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))

        # Extraire les données de la page
        page_data = extract_rows(driver)
        res.append(page_data)

        # Pause légère pour éviter d'être détecté comme bot
        time.sleep(0.5)

    # Concaténer toutes les pages dans un seul DataFrame
    df = pd.concat(res, ignore_index=True)

    return df

# Configuration du driver en mode headless
def get_headless_driver():
    """
    Initialise un driver Chrome en mode headless avec gestion automatique du ChromeDriver.
    """
    options = Options()
    options.add_argument("--headless")  # Mode sans fenêtre
    options.add_argument("--disable-gpu")  # Désactive l'accélération matérielle (utile sur certains OS)
    options.add_argument("--no-sandbox")  # Nécessaire pour certains environnements Linux
    options.add_argument("--disable-dev-shm-usage")  # Évite certains problèmes mémoire
    options.add_argument("--window-size=1920x1080")  # Définit une taille de fenêtre par défaut

    # Création du driver avec ChromeDriverManager
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def extract_name(chaine):
    """
    Extrait le nom (PA_xxx) d'une chaîne de caractères.

    Args:
        chaine (str): La chaîne de caractères à analyser.

    Returns:
        str: Le nom extrait ou None si la chaîne ne correspond pas au format attendu.
    """
    match = re.search(r"PA_\d+", chaine)
    return match.group(0) if match else None


def extract_points(chaine):
    """
    Extrait le nombre de points d'une chaîne de caractères.

    Args:
        chaine (str): La chaîne de caractères à analyser.

    Returns:
        int: Le nombre de points extrait ou None si la chaîne ne correspond pas au format attendu.
    """
    match = re.search(r"(\d+)\s+pts", chaine)
    return int(match.group(1)) if match else None


def extract_name_and_points(chaine):
    """
    Extrait le nom et le nombre de points d'une chaîne de caractères.

    Args:
        chaine (str): La chaîne de caractères à analyser.

    Returns:
        tuple: Un tuple contenant le nom et le nombre de points (sous forme d'entier).
               Retourne (None, None) si la chaîne ne correspond pas au format attendu.
    """
    match = re.search(r"<b>(PA_\d+)\s+\[(\d+)\s+pts\]</b>", chaine)
    if match:
        nom = match.group(1)
        points = int(match.group(2))
        return nom, points
    else:
        return None, None


def extract_district(chaine):
    """
    Extrait le nom et l'état d'une chaîne de caractères.

    Args:
        chaine (str): La chaîne de caractères à analyser.

    Returns:
        tuple: Un tuple contenant le nom et l'état.
               Retourne (None, None) si la chaîne ne correspond pas au format attendu.
    """
    match = re.search(r'<a href="javascript:lienv\(.+?\);">(.*?)<\/a>', chaine)
    if match:
        adresse = match.group(1)
        return adresse
    else:
        return None


def extract_state(text):
    """Fonction interne pour appliquer la regex."""
    if isinstance(text, str):
        match = re.search(r'>\s*([^<]+)$', text, re.MULTILINE) # Ajout du flag re.MULTILINE pour gérer les sauts de ligne
        if match:
            return match.group(1).strip() # Ajout de .strip() pour enlever les espaces en début et fin
    return None  # Retourne None si l'entrée n'est pas une chaîne ou si pas de correspondance


def generate_image_url(df):
    # Generate URLs for each image
    df = df[["0"]]
    df = df.rename(columns={"0":"relative_url_raw"})

    df['relative_url'] = df['relative_url_raw'].str.extract(r'<img[^>]*src="([^"]+)"', expand=False)
    df['url'] = "https://www.invader-spotter.art/" + df['relative_url']

    return df


# Function to download and save a PNG file
def download_png(url, save_dir):
    try:
        # Get the PNG name from the URL
        png_name = os.path.basename(url)
        # Full path to save the PNG file
        save_path = os.path.join(save_dir, png_name)

        # Check if the image already exists
        if os.path.exists(save_path):
            return # Skip to the next one


        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful

        # Save the content to a file
        with open(save_path, "wb") as file:
            file.write(response.content)

    except requests.exceptions.RequestException as e:
        print(f" (!) Failed to download {url}: {e}")
