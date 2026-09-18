from pathlib import Path
from typing import List, Optional
import sys
import re
import zipfile
import argparse
import tempfile
import shutil
import logging

try:
    import patoolib
    from patoolib import util
    PATOOL_AVAILABLE = True
except ImportError:
    patoolib = None
    util = None
    PATOOL_AVAILABLE = False

# =========================
# Configuration
# =========================

# Liste des fichiers .cbr ou .cbz à traiter.
# L'ordre détermine le numéro d'issue (1, 2, 3, ...).
# Exemples :
#   r"C:\Comics\issue1.cbr",
#   r"D:\Downloads\Spider-Man_02.cbz",
FICHIERS_CBR_CBZ = [
    # Ajoutez vos chemins de fichiers ici
    # r"C:\chemin\vers\issue1.cbr",
    # r"C:\chemin\vers\issue2.cbr",
    r"C:\Users\ebasson\Downloads\1.cbz",
    r"C:\Users\ebasson\Downloads\2.cbr",
    r"C:\Users\ebasson\Downloads\3.cbr",
    r"C:\Users\ebasson\Downloads\4.cbr",
    r"C:\Users\ebasson\Downloads\5.cbr",
]

# Titre du comic (optionnel, sinon prend le nom du premier fichier)
TITRE = "Old Man Wolverine"

# Dossier de destination (optionnel, sinon le répertoire courant)
CHEMIN_PARENT = r"C:\Users\ebasson\Documents\notes\Wiki\comics"

# Numéro de l'image à utiliser comme couverture
NUMERO_IMAGE_COUVERTURE = 1

SUPERHERO = "Wolverine"

PUBLISHER = "Marvel"

RELEASE_DATE = 2015

READ = False

# Extensions acceptées pour les images.
EXTENSIONS_IMAGES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".avif",
    ".bmp",
}


# =========================
# Fonctions utilitaires
# =========================

def nom_sans_caracteres_interdits(nom: str) -> str:
    nom = re.sub(r'[<>:"/\\|?*]', "-", nom)
    nom = nom.strip().rstrip(".")

    return nom or "comic"


# =========================
# Extraction des images
# =========================

def est_une_image(nom_fichier: str) -> bool:
    """Vérifie si un nom de fichier correspond à une image."""
    extension = Path(nom_fichier).suffix.lower()
    return extension in EXTENSIONS_IMAGES


def extraire_images_cbz(
        chemin_cbz: Path,
        dossier_destination: Path,
) -> int:
    """
    Extrait les images d'un fichier .cbz (zip).
    Retourne le nombre d'images extraites.
    """
    images_extraites = []

    try:
        with zipfile.ZipFile(chemin_cbz, 'r') as archive:
            fichiers = archive.namelist()

            # Trier les fichiers pour maintenir l'ordre
            fichiers_images = sorted(
                [f for f in fichiers if est_une_image(f)]
            )

            for index, nom_fichier in enumerate(fichiers_images, start=1):
                try:
                    donnees = archive.read(nom_fichier)
                    extension = Path(nom_fichier).suffix.lower()

                    nom_sortie = f"image-{index:03d}{extension}"
                    chemin_sortie = dossier_destination / nom_sortie

                    chemin_sortie.write_bytes(donnees)
                    images_extraites.append(nom_sortie)

                    print(f"[{index}/{len(fichiers_images)}] {nom_sortie}")

                except Exception as erreur:
                    print(
                        f"Erreur lors de l'extraction de {nom_fichier} : "
                        f"{erreur}",
                        file=sys.stderr,
                    )

        return len(images_extraites)

    except zipfile.BadZipFile as erreur:
        print(f"Erreur : {chemin_cbz} n'est pas un fichier ZIP valide.",
              file=sys.stderr)
        raise


def extraire_images_cbr(
        chemin_cbr: Path,
        dossier_destination: Path,
) -> int:
    """
    Extrait les images d'un fichier .cbr (rar).
    Utilise patool pour extraire.
    Retourne le nombre d'images extraites.
    """
    if not PATOOL_AVAILABLE:
        raise ImportError(
            "Le module 'patool' n'est pas installé. "
            "Installez-le avec : pip install patool"
        )

    images_extraites = []

    # Créer un dossier temporaire pour l'extraction
    with tempfile.TemporaryDirectory() as dossier_temp:
        try:
            # Désactiver les logs de patool
            logging.getLogger("patool").setLevel(logging.CRITICAL)

            # Extraire l'archive avec patool
            patoolib.extract_archive(
                str(chemin_cbr),
                outdir=dossier_temp,
                verbosity=-1,
            )

            # Chercher tous les fichiers images extraits
            fichiers_images = []
            for fichier in Path(dossier_temp).rglob("*"):
                if fichier.is_file() and est_une_image(fichier.name):
                    fichiers_images.append(fichier)

            # Trier les fichiers pour maintenir l'ordre
            fichiers_images = sorted(fichiers_images)

            for index, chemin_fichier in enumerate(fichiers_images, start=1):
                try:
                    extension = chemin_fichier.suffix.lower()
                    nom_sortie = f"image-{index:03d}{extension}"
                    chemin_sortie = dossier_destination / nom_sortie

                    # Copier le fichier
                    shutil.copy2(chemin_fichier, chemin_sortie)
                    images_extraites.append(nom_sortie)

                    print(f"[{index}/{len(fichiers_images)}] {nom_sortie}")

                except Exception as erreur:
                    print(
                        f"Erreur lors de l'extraction de {chemin_fichier.name} : "
                        f"{erreur}",
                        file=sys.stderr,
                    )

            return len(images_extraites)

        except Exception as erreur:
            print(f"Erreur : Impossible d'extraire {chemin_cbr} : {erreur}",
                  file=sys.stderr)
            raise


def extraire_images_archive(
        chemin_archive: Path,
        dossier_destination: Path,
) -> int:
    """Extrait les images selon le type de fichier (.cbr ou .cbz)."""
    extension = chemin_archive.suffix.lower()

    if extension == ".cbz":
        return extraire_images_cbz(chemin_archive, dossier_destination)
    elif extension == ".cbr":
        return extraire_images_cbr(chemin_archive, dossier_destination)
    else:
        raise ValueError(
            f"Format de fichier non supporté : {extension}. "
            f"Utilisez .cbr ou .cbz"
        )


# =========================
# Création des notes
# =========================

def creer_note_issue(
        dossier_comic: Path,
        issue: int,
        nombre_images: int,
        titre: str,
) -> None:
    """Crée une note Markdown pour une issue."""
    dossier_issue = dossier_comic / "images" / f"issue {issue}"

    numero_couverture = NUMERO_IMAGE_COUVERTURE

    fichiers_couverture = list(
        dossier_issue.glob(
            f"image-{numero_couverture:03d}.*"
        )
    )

    if fichiers_couverture:
        chemin_couverture = fichiers_couverture[0]
        couverture = (
            f"images/issue {issue}/"
            f"{chemin_couverture.name}"
        )
    else:
        print(
            f"Attention : image de couverture "
            f"{numero_couverture:03d} introuvable pour "
            f"l'issue {issue}.",
            file=sys.stderr,
        )
        couverture = ""

    lignes = [
        "---",
        "type: comic",
        f"title: {titre}",
        f"superhero: {SUPERHERO}",
        f"publisher: {PUBLISHER}",
        f"issue: {issue}",
        f"release_date: {RELEASE_DATE}",
        f"read: {str(READ).lower()}",
        f"cover: {couverture}",
        "tags:",
        "  - comics",
        "---",
        "",
        "# Lire",
        "",
    ]

    for numero in range(2, nombre_images + 1):
        fichiers_image = list(
            dossier_issue.glob(f"image-{numero:03d}.*")
        )

        if not fichiers_image:
            continue

        lignes.append(
            f"![[images/issue {issue}/{fichiers_image[0].name}]]"
        )

    nom_fichier = f"{titre} - Issue {issue}.md"
    chemin_fichier = dossier_comic / nom_fichier

    chemin_fichier.write_text(
        "\n".join(lignes) + "\n",
        encoding="utf-8",
    )

    print(f"Note créée : {chemin_fichier}")


# =========================
# Programme principal
# =========================

def traiter_archives(
        fichiers_archives: List[Path],
        dossier_sortie: Optional[Path] = None,
        titre: Optional[str] = None,
) -> None:
    """
    Traite une liste de fichiers .cbr ou .cbz.

    Args:
        fichiers_archives: Liste des chemins vers les fichiers .cbr/.cbz
        dossier_sortie: Dossier de destination (default: répertoire courant)
        titre: Titre du comic (default: nom du premier fichier)
    """
    if not fichiers_archives:
        raise ValueError("Aucun fichier fourni.")

    # Définir le dossier de sortie
    if dossier_sortie:
        dossier_sortie = Path(dossier_sortie).expanduser().resolve()
    else:
        dossier_sortie = Path.cwd()

    # Définir le titre
    if titre:
        titre = nom_sans_caracteres_interdits(titre)
    else:
        # Utiliser le nom du premier fichier sans extension
        titre = nom_sans_caracteres_interdits(
            fichiers_archives[0].stem
        )

    # Créer la structure des dossiers
    dossier_comic = dossier_sortie / titre
    dossier_images = dossier_comic / "images"

    dossier_comic.mkdir(parents=True, exist_ok=True)
    dossier_images.mkdir(parents=True, exist_ok=True)

    # Traiter chaque fichier comme une issue
    for numero_issue, chemin_archive in enumerate(fichiers_archives, start=1):
        chemin_archive = Path(chemin_archive).expanduser().resolve()

        if not chemin_archive.exists():
            print(
                f"Erreur : Le fichier {chemin_archive} n'existe pas.",
                file=sys.stderr,
            )
            continue

        print(f"\n=== Traitement de l'issue {numero_issue} : "
              f"{chemin_archive.name} ===")

        dossier_issue = dossier_images / f"issue {numero_issue}"
        dossier_issue.mkdir(parents=True, exist_ok=True)

        try:
            nombre_images = extraire_images_archive(
                chemin_archive,
                dossier_issue,
            )

            if nombre_images > 0:
                creer_note_issue(
                    dossier_comic=dossier_comic,
                    issue=numero_issue,
                    nombre_images=nombre_images,
                    titre=titre,
                )
            else:
                print(
                    f"Attention : Aucune image trouvée dans "
                    f"{chemin_archive.name}",
                    file=sys.stderr,
                )

        except (ValueError, ImportError, zipfile.BadZipFile) as erreur:
            print(
                f"Erreur lors du traitement de l'issue {numero_issue} : "
                f"{erreur}",
                file=sys.stderr,
            )
        except Exception as erreur:
            # Gérer les autres erreurs (patool, etc.)
            print(
                f"Erreur lors du traitement de l'issue {numero_issue} : "
                f"{erreur}",
                file=sys.stderr,
            )

    print(f"\n✓ Terminé. Dossier créé : {dossier_comic}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrait et organise les images des fichiers CBR/CBZ en "
                    "structure de comics."
    )

    parser.add_argument(
        "fichiers",
        nargs="*",
        help="Fichiers .cbr ou .cbz à traiter "
             "(l'ordre détermine le numéro d'issue). "
             "Si vide, utilise la liste FICHIERS_CBR_CBZ configurée.",
    )

    parser.add_argument(
        "-o", "--output",
        help="Dossier de destination (default: CHEMIN_PARENT ou répertoire courant)",
    )

    parser.add_argument(
        "-t", "--titre",
        help="Titre du comic (default: TITRE configuré ou nom du premier fichier)",
    )

    args = parser.parse_args()

    # Utiliser la liste configurée si aucun fichier n'est passé en paramètre
    fichiers_a_traiter = args.fichiers if args.fichiers else FICHIERS_CBR_CBZ

    # Utiliser les paramètres de ligne de commande ou les valeurs configurées
    titre = args.titre or (TITRE if TITRE else None)
    dossier_sortie = args.output or (CHEMIN_PARENT if CHEMIN_PARENT else None)

    try:
        if not fichiers_a_traiter:
            raise ValueError(
                "Aucun fichier fourni. Remplissez FICHIERS_CBR_CBZ dans le "
                "script ou passez des fichiers en paramètre."
            )

        traiter_archives(
            fichiers_archives=fichiers_a_traiter,
            dossier_sortie=dossier_sortie,
            titre=titre,
        )
    except (OSError, ValueError) as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()



