from pypresence import Presence
import time

client_id = "1373010800574333058"
RPC = Presence(client_id)
RPC.connect()

RPC.update(
    state="Grand Theft Auto VI - Campagne solo",
    details="GTA VI - Campagne solo",
    start=time.time(),
    large_image="gta.jpg",  # Le nom exact de l'image uploadée (expliqué ci-dessous)
    large_text="Grand Theft Auto VI"
)

print("RPC lancé. Appuie sur CTRL+C pour quitter.")
try:
    while True:
        time.sleep(15)
except KeyboardInterrupt:
    print("RPC arrêté.")
    RPC.clear()
