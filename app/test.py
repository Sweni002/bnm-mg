from PIL import Image
import os
import io

def reduire_image_png(image_path, sortie_path=None, taille_cible_ko=780):
    """
    Réduit un gros PNG (ex. 12 Mo) jusqu'à environ taille_cible_ko Ko
    en ajustant la résolution + la quantification des couleurs.
    """
    if not image_path.lower().endswith(".png"):
        raise ValueError("Ce script ne gère que les fichiers PNG.")

    # --- Préparation ---
    img = Image.open(image_path).convert("RGB")  # supprime la transparence pour mieux compresser
    largeur, hauteur = img.size
    base, _ = os.path.splitext(image_path)
    if not sortie_path:
        sortie_path = f"{base}_reduit.png"
    cible = taille_cible_ko * 1024

    # --- Fonction pour calculer la taille après compression ---
    def taille_png(img, compress_level=9):
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True, compress_level=compress_level)
        return len(buffer.getvalue()), buffer

    # --- Étape 1 : quantification des couleurs (jusqu'à 256) ---
    couleurs = 256
    img = img.convert("P", palette=Image.ADAPTIVE, colors=couleurs)

    # --- Étape 2 : compression + redimensionnement progressif ---
    taille, _ = taille_png(img)
    reduction = 0.9  # facteur de réduction de la taille à chaque itération

    while taille > cible and largeur > 200 and hauteur > 200:
        # Réduit la résolution
        largeur = int(largeur * reduction)
        hauteur = int(hauteur * reduction)
        img = img.resize((largeur, hauteur), Image.LANCZOS)
        # Réduit aussi les couleurs si nécessaire
        if couleurs > 64:
            couleurs = int(couleurs * 0.8)
            img = img.convert("P", palette=Image.ADAPTIVE, colors=couleurs)
        taille, buffer = taille_png(img, compress_level=6)
 
    # --- Sauvegarde finale ---
    with open(sortie_path, "wb") as f:
        f.write(buffer.getvalue())

    taille_originale = os.path.getsize(image_path) / 1024
    taille_finale = os.path.getsize(sortie_path) / 1024

    print(f"✅ Image réduite enregistrée : {sortie_path}")
    print(f"📦 Taille originale : {taille_originale:.1f} Ko ({taille_originale/1024:.2f} Mo)")
    print(f"📉 Taille finale : {taille_finale:.1f} Ko (≈ {taille_cible_ko} Ko cible)")
    print(f"🖼️ Résolution finale : {largeur}x{hauteur}")
    print(f"🎨 Nombre de couleurs : {couleurs}")

# Exemple d'utilisation
reduire_image_png("1.png", taille_cible_ko=780)
