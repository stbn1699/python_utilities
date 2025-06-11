def trouver_page_et_emplacement(numero_carte):
    if numero_carte < 1:
        return "Le numéro doit être supérieur ou égal à 1."

    page = (numero_carte - 1) // 9 + 1
    position = (numero_carte - 1) % 9 + 1
    return page, position

def main():
    try:
        numero = int(input("Entrez le numéro de la carte : "))
        resultat = trouver_page_et_emplacement(numero)
        if isinstance(resultat, tuple):
            page, position = resultat
            print(f"page {page}, position {position}.")
        else:
            print(resultat)
    except ValueError:
        print("Veuillez entrer un numéro valide.")

if __name__ == "__main__":
    main()
