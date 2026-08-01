#!/usr/bin/env python3
"""
Controllo interattivo della macchina Saeco via BLE.

Uso:
    python3 test3.py

Note importanti:
  - Il PIN e' DECIMALE e va passato come int. Lo zero iniziale
    mostrato sul display ("0389") e' solo padding: si scrive 389.
  - scan() crea il client SENZA pin, quindi bisogna chiamare
    pair() subito dopo connect(), prima di qualunque comando.
  - Dopo un AvantiPinError la libreria azzera il pin memorizzato:
    va rifatto pair() prima di riprovare.
  - Non riaccoppiare la macchina dalla GUI Bluetooth. Il bonding
    BlueZ causa "le-connection-abort-by-local".
    Se ricompare il timeout:  bluetoothctl remove <MAC>
"""

import logging
import time

from pysaeco import scan
from pysaeco.avanti import (
    AmericanCoffee,
    AvantiNoResponseError,
    AvantiPinError,
    Cappuccino,
    Coffee,
    Espresso,
)

# ----------------------------------------------------------------------
# Configurazione
# ----------------------------------------------------------------------

PIN = xxxx         # decimale, int. "0389" sul display si scrive 389
TENTATIVI = 6       # ritenta la connessione se l'adattatore fa i capricci
PAUSA = 3           # secondi tra un tentativo e l'altro

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logging.getLogger("bleak").setLevel(logging.WARNING)


# ----------------------------------------------------------------------
# Connessione
# ----------------------------------------------------------------------

def trova_macchina():
    print("Scansione in corso...")
    macchine = scan(timeout=10.0, name_prefix="SAECO")
    if not macchine:
        raise SystemExit("Nessuna macchina Saeco trovata. E' accesa e in range?")
    client = macchine[0]
    print(f"Trovata: {client.name} ({client.address})")
    return client


def connetti(client):
    for tentativo in range(1, TENTATIVI + 1):
        try:
            print(f"Connessione, tentativo {tentativo}...")
            client.connect()
            print("Connesso.")
            return True
        except Exception as e:
            print(f"  fallito: {type(e).__name__}")
            try:
                client.disconnect()
            except Exception:
                pass
            if tentativo < TENTATIVI:
                time.sleep(PAUSA)
    print("Connessione fallita dopo tutti i tentativi.")
    return False


def associa(client):
    """Imposta il PIN sul client. Necessario prima di ogni comando."""
    try:
        client.pair(PIN)
        return True
    except AvantiPinError:
        print(f"PIN {PIN} rifiutato dalla macchina.")
        return False
    except AvantiNoResponseError:
        print("Nessuna risposta: la macchina e' spenta? Prova prima l'opzione 1.")
        return False


# ----------------------------------------------------------------------
# Comandi
# ----------------------------------------------------------------------

RICETTE = {
    "espresso": lambda: Espresso(coffee_ml=45),
    "caffe": lambda: Coffee(coffee_ml=110),
    "americano": lambda: AmericanCoffee(coffee_ml=170),
    "cappuccino": lambda: Cappuccino(coffee_ml=70, milk_ml=70),
}


def mostra_stato(client):
    stato = client.read_status()
    print(f"\n  Alimentazione : {stato.power}")
    print(f"  In funzione   : {stato.running}")
    print(f"  Erogazione    : {stato.brew}")
    print(f"  Fase          : {stato.phase_name or stato.phase}")
    if stato.error:
        print(f"  ERRORE        : {stato.error}")
    if stato.warning:
        print(f"  Avvisi        : {', '.join(stato.warning)}")
    if stato.maintenance:
        print(f"  Manutenzione  : {stato.maintenance}")
    if stato.descaling_needed:
        print("  Serve decalcificare")
    print()


def eroga(client, nome_ricetta):
    ricetta = RICETTE[nome_ricetta]()
    print(f"Preparo: {ricetta.name} ({ricetta.coffee_ml} ml). Metti la tazzina!")
    client.brew(ricetta)
    print("Comando inviato.")


# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------

MENU = """
  1  Accendi (wakeup)
  2  Leggi stato
  3  Espresso 45 ml
  4  Caffe 110 ml
  5  Caffe americano 170 ml
  6  Cappuccino 70/70 ml
  7  Ferma erogazione
  8  Standby (spegni)
  9  Mostra PIN sul display macchina
  0  Esci
"""


def esegui(client, scelta):
    if scelta == "1":
        client.wakeup()
        print("Wakeup inviato. Attendo avvio...")
        time.sleep(5)
        associa(client)          # dopo l'accensione riassocia il pin
    elif scelta == "2":
        mostra_stato(client)
    elif scelta == "3":
        eroga(client, "espresso")
    elif scelta == "4":
        eroga(client, "caffe")
    elif scelta == "5":
        eroga(client, "americano")
    elif scelta == "6":
        eroga(client, "cappuccino")
    elif scelta == "7":
        client.stop_brewing()
        print("Erogazione fermata.")
    elif scelta == "8":
        client.standby()
        print("Macchina in standby.")
    elif scelta == "9":
        client.show_pin()
        print("Guarda il display della macchina.")
    else:
        print("Scelta non valida.")


def main():
    client = trova_macchina()

    if not connetti(client):
        return

    # Il client creato da scan() non ha pin: va impostato subito,
    # altrimenti ogni comando fallisce con "PIN is required".
    if associa(client):
        print("PIN accettato.")
    else:
        print("Prova l'opzione 1 per accendere, oppure la 9 per vedere il PIN.")

    try:
        while True:
            print(MENU)
            scelta = input("Scelta: ").strip()
            if scelta == "0":
                break

            try:
                esegui(client, scelta)

            except AvantiPinError:
                # La libreria azzera il pin al primo errore: va rimesso.
                print("PIN rifiutato, riprovo l'associazione...")
                if associa(client):
                    print("Riassociato. Rilancia il comando.")
                else:
                    print(f"PIN {PIN} non valido. Usa l'opzione 9 per vederlo.")

            except AvantiNoResponseError:
                print("Nessuna risposta. La macchina e' accesa? Prova l'opzione 1.")

            except Exception as e:
                print(f"Errore: {type(e).__name__}: {e}")

    except (KeyboardInterrupt, EOFError):
        print("\nInterrotto.")
    finally:
        try:
            client.disconnect()
            print("Disconnesso.")
        except Exception:
            pass


if __name__ == "__main__":
    main()
