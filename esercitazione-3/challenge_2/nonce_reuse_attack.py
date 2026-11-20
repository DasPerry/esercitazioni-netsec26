import sys

OFFSET = 8 + 20 + 20   # LLC/SNAP(8) + IP header(20, no options) + TCP header(20, no options)
                        # == offset del body applicativo dentro il campo "Data" (CCMP header escluso)

def load_frames(path):
    frames = []
    with open(path) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4 or not parts[3]:
                continue
            frame_no, pn_hex, length, data_hex = parts[0], parts[1], parts[2], parts[3]
            frames.append({
                "frame": frame_no,
                "pn": pn_hex,
                "len": int(length),
                "data": bytes.fromhex(data_hex),
            })
    return frames

def main():
    tsv_path, file_path = sys.argv[1], sys.argv[2]
    frames = load_frames(tsv_path)

    with open(file_path, "rb") as f:
        known_plaintext = f.read()

    # 1) trova i PN ripetuti
    by_pn = {}
    for fr in frames:
        by_pn.setdefault(fr["pn"], []).append(fr)

    dup_pns = {pn: lst for pn, lst in by_pn.items() if len(lst) > 1}
    print(f"PN ripetuti trovati: {list(dup_pns.keys())}")

    # 2) tra le coppie con PN ripetuto, cerca quella il cui frame più vecchio
    #    ha una regione payload (dopo OFFSET) lunga quanto il file noto
    target_pn = None
    for pn, lst in dup_pns.items():
        lst_sorted = sorted(lst, key=lambda x: int(x["frame"]))
        first = lst_sorted[0]
        payload_region_len = len(first["data"]) - OFFSET - 8  # -8 per il MIC finale
        if payload_region_len == len(known_plaintext):
            target_pn = pn
            print(f"Trovata coppia utile: PN={pn}, frame {[f['frame'] for f in lst_sorted]}")
            break

    if target_pn is None:
        print("Nessuna coppia con lunghezza payload coincidente trovata. "
              "Controlla OFFSET (header IP/TCP potrebbero avere opzioni) o i frame in input.")
        return

    lst_sorted = sorted(dup_pns[target_pn], key=lambda x: int(x["frame"]))
    frame_upload = lst_sorted[0]   # prima del tempo = prima dell'attacco (upload noto)
    frame_login = lst_sorted[1]    # dopo l'attacco (quello da decifrare)

    C1 = frame_upload["data"]
    C2 = frame_login["data"]

    c1_region = C1[OFFSET: OFFSET + len(known_plaintext)]
    keystream = bytes(a ^ b for a, b in zip(c1_region, known_plaintext))

    # sanity check
    assert bytes(a ^ b for a, b in zip(c1_region, keystream)) == known_plaintext

    c2_region = C2[OFFSET:]
    n = min(len(keystream), len(c2_region))
    recovered = bytes(a ^ b for a, b in zip(c2_region[:n], keystream[:n]))

    print(f"\n--- Recuperato da frame {frame_login['frame']} (PN={target_pn}) ---")
    print(recovered.decode("latin1"))

    # estrai la flag se presente
    import re
    m = re.search(rb"netsec\{[^}]*\}", recovered)
    if m:
        print(f"\nFLAG: {m.group(0).decode()}")

if __name__ == "__main__":
    main()
