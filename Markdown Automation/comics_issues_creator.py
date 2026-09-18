from pathlib import Path
from urllib.parse import urljoin, urlparse
import mimetypes
import re
import sys

import requests
from bs4 import BeautifulSoup

# =========================
# Configuration
# =========================

TITRE = ""

NOMBRE_ISSUES = 0

NUMERO_IMAGE_COUVERTURE = 1

CHEMIN_PARENT = r""

SUPERHERO = ""

PUBLISHER = ""

RELEASE_DATE = 0

READ = False

# Une URL par issue.
# La première URL correspond à l'issue 1,
# la deuxième à l'issue 2, etc.
URLS_ISSUES = [
    "https://readfreecomicsonline.com/spider-man-wolverine-issue-1-2003/",
    "https://readfreecomicsonline.com/spider-man-wolverine-issue-2-2003/",
    "https://readfreecomicsonline.com/spider-man-wolverine-issue-3-2003/",
    "https://readfreecomicsonline.com/spider-man-wolverine-issue-4-2003/",
]

# Sélecteur CSS des images à récupérer.
# "img" récupère toutes les balises <img>.
SELECTEUR_IMAGES = "img"

# Attributs utilisés par les sites pour les images différées.
ATTRIBUTS_IMAGES = [
    "src",
    "data-src",
    "data-original",
    "data-lazy-src",
    "data-image",
]

# Extensions acceptées pour les images.
EXTENSIONS_IMAGES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".avif",
}

# Délai entre deux téléchargements.
DELAI_ENTRE_REQUETES = 0.01

# Nombre de secondes avant abandon d'une requête.
TIMEOUT = (10, 60)


# =========================
# Fonctions utilitaires
# =========================

def nom_sans_caracteres_interdits(nom: str) -> str:
    nom = re.sub(r'[<>:"/\\|?*]', "-", nom)
    nom = nom.strip().rstrip(".")

    return nom or "comic"


def extraire_url_image(
        image,
        url_page: str,
) -> str | None:
    """
    Récupère l'URL la plus pertinente d'une balise <img>.
    """

    # On donne la priorité aux attributs contenant normalement
    # l'image réellement chargée ou l'image différée.
    for attribut in ATTRIBUTS_IMAGES:
        valeur = image.get(attribut)

        if valeur and not valeur.startswith("data:"):
            return urljoin(url_page, valeur.strip())

    # Fallback : essayer srcset.
    srcset = image.get("srcset")

    if srcset:
        candidats = []

        for element in srcset.split(","):
            morceaux = element.strip().split()

            if not morceaux:
                continue

            url = urljoin(url_page, morceaux[0])
            largeur = 0

            if len(morceaux) > 1 and morceaux[1].endswith("w"):
                try:
                    largeur = int(morceaux[1][:-1])
                except ValueError:
                    largeur = 0

            candidats.append((largeur, url))

        if candidats:
            return max(candidats, key=lambda candidat: candidat[0])[1]

    return None


def est_probablement_une_image(url: str) -> bool:
    chemin = urlparse(url).path.lower()
    extension = Path(chemin).suffix

    return extension in EXTENSIONS_IMAGES


def extension_depuis_reponse(
        reponse: requests.Response,
        url: str,
) -> str:
    """
    Détermine l'extension à partir du Content-Type,
    avec fallback sur l'URL.
    """

    content_type = reponse.headers.get("Content-Type", "")
    content_type = content_type.split(";")[0].strip()

    extension = mimetypes.guess_extension(content_type)

    if extension:
        if extension == ".jpe":
            return ".jpg"

        return extension

    extension_url = Path(urlparse(url).path).suffix.lower()

    if extension_url in EXTENSIONS_IMAGES:
        return extension_url

    return ".bin"


# =========================
# Téléchargement des images
# =========================

def recuperer_images_issue(
        session: requests.Session,
        url_page: str,
        dossier_issue: Path,
) -> int:
    print(f"\nAnalyse de la page : {url_page}")

    reponse_page = session.get(
        url_page,
        timeout=TIMEOUT,
    )
    reponse_page.raise_for_status()

    soup = BeautifulSoup(
        reponse_page.text,
        "html.parser",
    )

    images_trouvees = []
    urls_deja_vues = set()

    for image in soup.select(SELECTEUR_IMAGES):
        url_image = extraire_url_image(image, url_page)

        if not url_image:
            continue

        if url_image in urls_deja_vues:
            continue

        if not est_probablement_une_image(url_image):
            continue

        urls_deja_vues.add(url_image)
        images_trouvees.append(url_image)

    print(f"{len(images_trouvees)} image(s) trouvée(s).")

    nombre_telecharge = 0

    for index, url_image in enumerate(images_trouvees, start=1):
        try:
            reponse_image = session.get(
                url_image,
                stream=True,
                timeout=TIMEOUT,
            )
            reponse_image.raise_for_status()

            extension = extension_depuis_reponse(
                reponse_image,
                url_image,
            )

            nom_fichier = (
                f"image-{index:03d}{extension}"
            )

            chemin_fichier = dossier_issue / nom_fichier

            with chemin_fichier.open("wb") as fichier:
                for bloc in reponse_image.iter_content(
                        chunk_size=1024 * 128
                ):
                    if bloc:
                        fichier.write(bloc)

            nombre_telecharge += 1

            print(
                f"[{nombre_telecharge}/{len(images_trouvees)}] "
                f"{nom_fichier}"
            )

        except requests.RequestException as erreur:
            print(
                f"Erreur pour l'image {url_image} : {erreur}",
                file=sys.stderr,
            )

    return nombre_telecharge


# =========================
# Création des notes
# =========================

def creer_note_issue(
        dossier_comic: Path,
        issue: int,
        nombre_images: int,
) -> None:
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
        f"title: {TITRE}",
        f"superhero: {SUPERHERO}",
        f"publisher: {PUBLISHER}",
        f"issue: {issue}",
        f"release_date: {RELEASE_DATE}",
        f"read: {str(READ).lower()}",
        f"cover: {couverture}",
        "tags:",
        "  - comics",
        "  - marvel",
        "  - spider-man",
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

    nom_fichier = f"{TITRE} - Issue {issue}.md"
    chemin_fichier = dossier_comic / nom_fichier

    chemin_fichier.write_text(
        "\n".join(lignes) + "\n",
        encoding="utf-8",
    )

    print(f"Note créée : {chemin_fichier}")


# =========================
# Programme principal
# =========================

def main() -> None:
    if NOMBRE_ISSUES < 1:
        raise ValueError(
            "NOMBRE_ISSUES doit être supérieur ou égal à 1."
        )

    if len(URLS_ISSUES) != NOMBRE_ISSUES:
        raise ValueError(
            "Le nombre d'URL dans URLS_ISSUES doit être égal "
            "à NOMBRE_ISSUES."
        )

    titre_dossier = nom_sans_caracteres_interdits(TITRE)

    dossier_comic = (
            Path(CHEMIN_PARENT).expanduser().resolve()
            / titre_dossier
    )

    dossier_images = dossier_comic / "images"

    dossier_comic.mkdir(
        parents=True,
        exist_ok=True,
    )

    dossier_images.mkdir(
        parents=True,
        exist_ok=True,
    )

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,"
                  "application/xml;q=0.9,image/avif,"
                  "image/webp,*/*;q=0.8",
    })

    for issue, url_page in enumerate(URLS_ISSUES, start=1):
        dossier_issue = dossier_images / f"issue {issue}"

        dossier_issue.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            nombre_images = recuperer_images_issue(
                session=session,
                url_page=url_page,
                dossier_issue=dossier_issue,
            )

            creer_note_issue(
                dossier_comic=dossier_comic,
                issue=issue,
                nombre_images=nombre_images,
            )

        except requests.RequestException as erreur:
            print(
                f"Impossible de traiter l'issue {issue} : {erreur}",
                file=sys.stderr,
            )

    print(
        f"\nTerminé. Dossier créé : {dossier_comic}"
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        sys.exit(1)
