import math

def trouver_page_et_emplacement(numero_carte):
	if numero_carte < 1:
		return "Le numéro doit être supérieur ou égal à 1."

	page = (numero_carte - 1) // 9 + 1
	position = (numero_carte - 1) % 9 + 1
	vraie_page = math.ceil(page / 2)
	face = "recto" if page % 2 == 0 else "verso"

	return page, position, vraie_page, face

def main():
	while True:
		entree = input("Entrez le numéro de la carte (ou 'exit' pour quitter) : ").strip().lower()

		if entree == "exit":
			print("Fermeture du programme.")
			break

		if not entree.isdigit():
			print("Veuillez entrer un numéro valide.")
			continue

		numero = int(entree)
		resultat = trouver_page_et_emplacement(numero)

		if isinstance(resultat, tuple):
			page, position, vraie_page, face = resultat
			print(f"\tCarte n°{numero} → Page {page} ({vraie_page}, {face}), Position {position}/9\n")
		else:
			print(resultat)

if __name__ == "__main__":
	main()
