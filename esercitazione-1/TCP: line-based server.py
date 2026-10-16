import socket
import threading

# 1. Definiamo il dizionario globale per il key-value store (visibile da tutte le connessioni)
KV_STORE = {}

def gestisci_client(client_socket, client_address):
    buffer = ""
    try:
        while True:
            dati = client_socket.recv(1024)
            if not dati:
                break

            # Aggiungiamo i dati ricevuti al buffer del client decodificandoli in utf-8
            buffer += dati.decode('utf-8')

            # Finché nel buffer c'è un carattere di fine linea '\n', estraiamo una riga completa
            while '\n' in buffer:
                # Separiamo la prima riga dal resto del buffer
                linea, buffer = buffer.split('\n', 1)

                # Puliamo la linea da eventuali spazi o ritorni a capo residui (\r)
                messaggio = linea.strip()
                if not messaggio:
                    continue  # Salta righe vuote

                print(f"[{client_address}] Ricevuto: {messaggio}")

                # Divisione del comando dai parametri
                parts = messaggio.split(' ', 1)
                cmd = parts[0]

                # Logica dei comandi (PING, ECHO, SET, GET)
                if cmd == "PING":
                    risposta = "PONG\n"

                elif cmd == "ECHO":
                    if len(parts) > 1:
                        risposta = f"{parts[1]}\n"
                    else:
                        risposta = "ERR\n"

                elif cmd == "SET":
                    if len(parts) > 1 and ' ' in parts[1]:
                        key, value = parts[1].split(' ', 1)
                        KV_STORE[key] = value
                        risposta = "OK\n"
                    else:
                        risposta = "ERR\n"

                elif cmd == "GET":
                    if len(parts) > 1:
                        key = parts[1].strip()
                        if key in KV_STORE:
                            risposta = f"{KV_STORE[key]}\n"
                        else:
                            risposta = "NOT_FOUND\n"
                    else:
                        risposta = "ERR\n"

                else:
                    risposta = "ERR\n"

                # Invio della risposta al client
                client_socket.sendall(risposta.encode('utf-8'))

    except Exception as e:
        print(f"Errore con {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"Connessione chiusa con {client_address}\n")

def avvia_server():
    # 2. Creazione del socket TCP (AF_INET = IPv4, SOCK_STREAM = TCP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Permette di riutilizzare la porta immediatamente dopo la chiusura
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 3. Binding del server su tutte le interfacce (incluso l'esterno/VPN) sulla porta 9001
    server_socket.bind(('0.0.0.0', 9001))

    # 4. Mettiamo il server in ascolto
    server_socket.listen(5)
    print("Server in ascolto sulla porta 9001...")

    try:
        while True:
            # 5. Accettiamo una connessione in arrivo da un client
            client_socket, client_address = server_socket.accept()
            print(f"Connessione stabilita con {client_address}")

            # Avviamo il thread per gestire il client in concorrenza
            client_thread = threading.Thread(target=gestisci_client, args=(client_socket, client_address))
            client_thread.start()

    except KeyboardInterrupt:
        print("\nChiusura del server...")
        server_socket.close()

if __name__ == "__main__":
    avvia_server()
