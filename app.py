from flask import Flask, render_template, jsonify
import base64
import folium
from folium.plugins import MarkerCluster
from folium import LayerControl
import pandas as pd
import numpy as np


app = Flask(__name__)


def create_colored_map_filtered_captured(
    df,
    latitude_col='Latitude',
    longitude_col='Longitude',
    state_col='state',
    tiles='OpenStreetMap',
    attr=None,
    image_col='image_path',
    number_col = 'number',
    name_col='invader_name',
    captured_col='captured'
):
    """
    Crée une carte folium avec des cercles colorés, filtrage optionnel des points capturés.

    Points non capturés (captured=False) sont TOUJOURS affichés.
    Points capturés (captured=True) sont dans une couche optionnelle (LayerControl).

    Args:
        ... (documentation mise à jour) ...
    """

    # Définir un dictionnaire pour les couleurs en fonction de l'état (pour le remplissage par défaut)
    state_colors = {
        'OK': 'green',
        'Un peu dégradé': 'yellow',
        'Détruit !': 'black',
        'Dégradé': 'orange',
        'Très dégradé': 'red',
        'Non visible': 'gray',
        None: 'lightgray'
    }

    # Extraire les données
    latitudes = df[latitude_col].tolist()
    longitudes = df[longitude_col].tolist()
    states = df[state_col].tolist()
    numbers = df[number_col].astype(int).tolist()
    names = df[name_col].tolist()
    captured_statuses = df[captured_col].tolist()

    # Calculer le centre de la carte
    map_center_lat = sum(latitudes) / len(latitudes)
    map_center_lon = sum(longitudes) / len(longitudes)

    # Déterminer si c'est une url
    is_url = tiles.startswith('http://') or tiles.startswith('https://')

    # Créer la carte
    if is_url:
      if not attr:
        raise Exception("Custom tiles must have an attribution")
      carte = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=12, tiles=tiles, attr=attr)
    else:
        carte = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=12, tiles=tiles)

    # Créer des groupes de marqueurs séparés pour points non capturés et capturés
    marker_cluster_uncaptured = MarkerCluster(name='Points à capturer (non capturés)').add_to(carte) # Groupe pour les points non capturés, TOUJOURS visible
    marker_cluster_captured = MarkerCluster(name='Points capturés', show=False).add_to(carte) # Groupe pour les points capturés, optionnel (show=False pour qu'il soit décoché par défaut)


    # Ajouter un cercle pour chaque point
    if image_col and name_col:
        images = df[image_col].tolist()

        for lat, lon, state, image, number, name, captured in zip(latitudes, longitudes, states, images, numbers, names, captured_statuses):
            # Déterminer la couleur de remplissage (bleu si capturé, sinon basé sur l'état)
            fill_color = 'blue' if captured else state_colors.get(state, 'lightgray')
            border_color = 'blue' if captured else state_colors.get(state, 'lightgray')

            # Lien Instagram
            instagram_link = f'<p style="text-align:center"><a href="https://www.instagram.com/explore/tags/{name.replace("#", "").replace(" ", "")}/" target="_blank"><b>{name}</b></a><span> - {state}</span></p>'

            # Popup avec image
            try:
                with open(image, "rb") as f:
                    image_base64 = base64.b64encode(f.read()).decode("utf-8")
                html = f'{instagram_link}<img src="data:image/png;base64,{image_base64}" width="150"><br><button id="capture_btn_{number}">Capturer !</button>'
                popup = folium.Popup(html, max_width=250)
            except FileNotFoundError:
                html = f'{instagram_link}<br><button id="capture_btn_{number}">Capturer !</button><p>Image {image} not found</p>' # Ajout du bouton ici aussi
                popup = folium.Popup(html, max_width=250)

            circle = folium.Circle(
              location=[lat, lon],
              radius=100,
              color=border_color,
              fill=True,
              fill_color=fill_color,
              fill_opacity=0.4,
              popup = popup,
              weight=3
            )
            if captured:
                circle.add_to(marker_cluster_captured) # Ajouter au groupe "Points capturés" SI captured=True
            else:
                circle.add_to(marker_cluster_uncaptured) # Sinon, ajouter au groupe "Points à capturer"


    elif image_col : # le cas ou la colonne de nom n'est pas précisée
        images = df[image_col].tolist()
        for lat, lon, state, image, captured in zip(latitudes, longitudes, states, images, captured_statuses):
            fill_color = 'blue' if captured else state_colors.get(state, 'lightgray')
            border_color = 'blue' if captured else state_colors.get(state, 'lightgray')

            try:
                with open(image, "rb") as f:
                    image_base64 = base64.b64encode(f.read()).decode("utf-8")
                html = f'<img src="data:image/png;base64,{image_base64}" width="150">'
                popup = folium.Popup(html, max_width=250)
            except FileNotFoundError:
                popup = folium.Popup(f"Image {image} not found", max_width=150)

            circle = folium.Circle(
              location=[lat, lon],
              radius=100,
              color=border_color,
              fill=True,
              fill_color=fill_color,
              fill_opacity=0.4,
              popup = popup,
              weight=3
            )
            if captured:
                circle.add_to(marker_cluster_captured) # Ajouter au groupe "Points capturés" SI captured=True
            else:
                circle.add_to(marker_cluster_uncaptured) # Sinon, ajouter au groupe "Points à capturer"


    else: # Cas sans image
        for lat, lon, state, name, captured in zip(latitudes, longitudes, states, names, captured_statuses):
            fill_color = 'blue' if captured else state_colors.get(state, 'lightgray')
            border_color = 'blue' if captured else state_colors.get(state, 'lightgray')
            instagram_link = f'<p style="text-align:center"><a href="https://www.instagram.com/explore/tags/{name.replace("#", "").replace(" ", "")}/" target="_blank"><b>{name}</b></a><span> - {state}</span></p>'
            popup = folium.Popup(instagram_link, max_width=250)

            circle = folium.Circle(
                location=[lat, lon],
                radius=50,
                color=border_color,
                fill=True,
                fill_color=fill_color,
                fill_opacity=0.4,
                popup=popup,
                weight=3
            )
            if captured:
                circle.add_to(marker_cluster_captured) # Ajouter au groupe "Points capturés" SI captured=True
            else:
                circle.add_to(marker_cluster_uncaptured) # Sinon, ajouter au groupe "Points à capturer"

    LayerControl().add_to(carte) # Ajouter le contrôle des couches à la carte

    return carte


def generate_image_name(number):
    num = "{:04d}".format(number)
    return "img/PA_" + num + "-grosplan.png"


def create_colored_map_interactive_capture(
    df,
    latitude_col='Latitude',
    longitude_col='Longitude',
    state_col='state',
    tiles='OpenStreetMap',
    attr=None,
    image_col='image_path',
    name_col='invader_name',
    captured_col='captured'
):
    """
    Crée une carte folium INTERACTIVE avec bouton "Capturé" dans les popups.

    Points non capturés (captured=False) sont TOUJOURS affichés initialement.
    Points capturés (captured=True) sont dans une couche optionnelle (LayerControl).
    Bouton "Capturé" dans la popup pour marquer un point comme capturé (modification visuelle côté client).

    Args:
        ... (documentation mise à jour) ...
    """

    # Définir un dictionnaire pour les couleurs en fonction de l'état (pour le remplissage par défaut)
    state_colors = {
        'OK': 'green',
        'Un peu dégradé': 'yellow',
        'Détruit !': 'black',
        'Dégradé': 'orange',
        'Très dégradé': 'red',
        'Non visible': 'gray',
        None: 'lightgray'
    }

    # Extraire les données des colonnes du DataFrame
    latitudes = df[latitude_col].tolist()
    longitudes = df[longitude_col].tolist()
    states = df[state_col].tolist()
    names = df[name_col].tolist()
    captured_statuses = df[captured_col].tolist()
    if image_col: # Vérifie si la colonne image_col est spécifiée (pour éviter erreur si non présente)
        images = df[image_col].tolist()
    else:
        images = [None] * len(df) # Liste de None si pas de colonne image

    # Calculer le centre de la carte pour un affichage initial centré
    map_center_lat = sum(latitudes) / len(latitudes) if latitudes else 48.85 # Centre par défaut si pas de latitudes
    map_center_lon = sum(longitudes) / len(longitudes) if longitudes else 2.35 # Centre par défaut si pas de longitudes

    # Déterminer si le 'tiles' est une URL ou un nom de style Folium
    is_url = tiles.startswith('http://') or tiles.startswith('https://')

    # Créer la carte Folium
    if is_url:
        if not attr:
            raise Exception("Custom tiles must have an attribution (attr)") # Sécurité : attribution requise pour tiles URL
        carte = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=12, tiles=tiles, attr=attr)
    else:
        carte = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=12, tiles=tiles) # Tiles Folium standard

    # Créer des groupes de marqueurs (MarkerCluster) pour optimiser l'affichage et le LayerControl
    marker_cluster_uncaptured = MarkerCluster(name='Points à capturer (non capturés)').add_to(carte)
    marker_cluster_captured = MarkerCluster(name='Points capturés', show=False).add_to(carte) # 'show=False' pour décocher par défaut

    # Javascript pour le bouton "Capturé" (reste inchangé - c'est le même Javascript fonctionnel)
    js_capture_button = """
    function(btn, circle_id) {
        btn.addEventListener('click', function() {
            alert('Bouton cliqué !'); // Affiche une alerte TRÈS BASIQUE
        });
    }
    """

    # Boucle sur les données pour créer un cercle + popup + bouton pour chaque point
    for i, (lat, lon, state, image, name, captured) in enumerate(zip(latitudes, longitudes, states, images, names, captured_statuses)):
        # Couleur de remplissage initiale du cercle (bleu si déjà capturé, sinon selon l'état)
        fill_color = 'blue' if captured else state_colors.get(state, 'lightgray')
        border_color = 'blue' if captured else state_colors.get(state, 'lightgray')

        # Construction du contenu HTML de la popup
        instagram_link = "" # Initialiser à vide par défaut
        # if pd.isna(name) or name is None: # Sécurité : gestion des noms manquants (None/NaN)
        #     instagram_link = '<p style="text-align:center"><b>Invader inconnu</b><span> - {state}</span></p>' # Nom par défaut
        # else:
        #     instagram_link = f'<p style="text-align:center"><a href="https://www.instagram.com/explore/tags/{name.replace("#", "").replace(" ", "")}/" target="_blank"><b>{name}</b></a><span> - {state}</span></p>'

        image_html = "" # Initialiser à vide par défaut
        if image: # Vérifier si un chemin d'image est fourni
            try:
                with open(image, "rb") as f:
                    image_base64 = base64.b64encode(f.read()).decode("utf-8")
                image_html = f'<img src="data:image/png;base64,{image_base64}" width="150"><br>' # HTML pour l'image
            except FileNotFoundError:
                image_html = f'<p>Image {image} non trouvée</p><br>' # Message si image non trouvée

        html_content = f'{instagram_link}{image_html}<button id="capture_btn_{i}">Capturer !</button>' # Popup: lien Insta, image (si dispo), bouton
        popup = folium.Popup(html_content, max_width=250)

        # Créer le cercle Folium pour chaque point
        circle = folium.Circle(
            location=[lat, lon],
            radius=100, # Rayon des cercles
            color=border_color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.4, # Opacité du remplissage
            popup=popup, # Associer la popup au cercle
            weight=3 # Épaisseur de la bordure
        )

        if captured:
            circle.add_to(marker_cluster_captured) # Ajouter au groupe "Points capturés" SI captured=True
        else:
            circle.add_to(marker_cluster_uncaptured) # Sinon, groupe "Points à capturer"

        # Ajouter le popup comme enfant du cercle (nécessaire pour que le script fonctionne correctement)
        circle.add_child(folium.Popup(popup))

        # Injecter le script Javascript pour chaque bouton, en utilisant un ID unique et l'ID Leaflet du cercle
        carte.add_child(folium.Element(f"""
            <script>
                var btn_{{number}} = document.querySelector('#capture_btn_{{number}}');
                if (btn_{{number}}) {{
                    var capture_function_{i} = {js_capture_button};
                    capture_function_{i}(btn_{{number}}, '{circle.get_name()}', '{name}');
                }}
            </script>
        """))


    LayerControl().add_to(carte) # Ajouter le contrôle des couches à la carte (pour activer/désactiver les points capturés)

    return carte # Retourner l'objet carte Folium créé


@app.route('/')
def index():

    # Coordinates for each SI from 1 to 1523
    data_complete = pd.read_csv('data/paris_invaders_1523.csv')

    # Updated data for each SI from 1 to 1531
    data_spotter = pd.read_excel("data/20250125_export_invader_spotter_art_listing.xlsx")
    data_spotter = data_spotter[['name', 'points', 'district', 'state']]

    # df1 = données GPS
    df1 = data_complete
    # df2 = données d'Invader Spotter à jour
    df2 = data_spotter[['name','state']]
    # Rassembler les données dans un dataframe
    df = df1.merge(df2, left_on='invader_name', right_on='name')
    # Ajouter une colonne capturée (il en faudra une vraie)
    df["captured"] = False

    # Ajouter de l'incertitude : chiffre de coordonnées aléatoire à 10^(-4) pour déplacer un peu le point
    random_list = np.random.uniform(-0.0004, 0.0004, len(df)).tolist()
    df['Latitude'] = df['Latitude'].round(4) + random_list
    df['Longitude'] = df['Longitude'].round(4) + random_list

    # Générer des noms d'images pour aller les chercher dans l'ordi
    df['image_path'] = df['number'].astype(int).apply(generate_image_name)

    # Fonctions
    # create_colored_map_filtered_captured
    # create_colored_map_interactive_capture
    carte_invaders = create_colored_map_filtered_captured(
        df,
        image_col='image_path',
        name_col='invader_name',
        # tiles='https://tile.jawg.io/jawg-lagoon/{z}/{x}/{y}{r}.png?access-token=8wFTNarg88jGskijTyyNfdlyq8jQSbQF0zI0lXwhUXW56LISiGyW2RsJpF3HJZXj',
        # attr= 'Jawg.Lagoon',
        tiles='CartoDB positron',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    )

    carte_html = ""
    try:
        carte_html = carte_invaders._repr_html_()
    except Exception as e:
        print("Erreur lors de la conversion de la carte en HTML:", e)
        carte_html = "<p>Erreur lors du chargement de la carte.</p>"
    return render_template('index.html', carte_invaders_html=carte_html)


@app.route('/capture_invader/<invader_number>', methods=['POST']) # Route pour gérer les requêtes de capture (POST uniquement)
def capture_invader(invader_number):
    print(f"Requête de capture reçue pour Invader #{invader_number}") # Log sur le serveur
    return jsonify({'status': 'success', 'message': f'Invader #{invader_number} marqué comme capturé (côté serveur - pas encore implémenté)'}) # Réponse JSON au client


if __name__ == '__main__':
    app.run(debug=True)