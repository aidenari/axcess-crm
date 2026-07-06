import httpx
import sys

BASE_URL = "http://127.0.0.1:8001"

def run():
    # 1. Create temporary programme and batiment to hold the lot (to be safe)
    # Actually, let's just use existing ones if possible, or create new structure.
    # Create Programme
    resp = httpx.post(f"{BASE_URL}/programmes", json={"nom": "Test Prog temp"})
    if resp.status_code != 201:
        print("Failed to create programme", resp.text)
        return
    prog_id = resp.json()["id"]

    # Create Batiment
    resp = httpx.post(f"{BASE_URL}/batiments", json={"programme_id": prog_id, "nom": "Bat A"})
    if resp.status_code != 201:
        print("Failed to create batiment", resp.text)
        return
    bat_id = resp.json()["id"]

    # Create Client
    resp = httpx.post(f"{BASE_URL}/clients", json={"last_name": "TestClient", "first_name": "TOTO", "email": "test@example.com"})
    if resp.status_code != 201:
        print("Failed to create client", resp.text)
        return
    client_id = resp.json()["id"]
    print(f"Created Client ID: {client_id}")

    # Create Lot
    resp = httpx.post(f"{BASE_URL}/lots", json={"batiment_id": bat_id, "lot": "A101", "acquereur": ""})
    lot_id = resp.json()["id"]
    print(f"Created Lot ID: {lot_id} with no acquereur")

    # Verify initial state
    resp = httpx.get(f"{BASE_URL}/lots", params={"batiment_id": bat_id})
    lot = [l for l in resp.json() if l["id"] == lot_id][0]
    print(f"Initial: client_id={lot.get('client_id')}, acquereur='{lot.get('acquereur')}'")

    # 2. Update Lot to assign client
    payload = {
        "client_id": client_id,
        "acquereur": "TestClient TOTO"
    }
    resp = httpx.put(f"{BASE_URL}/lots/{lot_id}", json=payload)
    if resp.status_code != 200:
        print("Failed to update lot with client", resp.text)
        return
    
    lot = resp.json()
    print(f"After Assignment: client_id={lot.get('client_id')}, acquereur='{lot.get('acquereur')}'")
    if lot.get("client_id") != client_id:
        print("ERROR: Client ID not set!")

    # 3. Update Lot to remove client (Simulate 'Aucun')
    # Use null for client_id and empty string for acquereur
    payload = {
        "client_id": None,
        "acquereur": ""
    }
    resp = httpx.put(f"{BASE_URL}/lots/{lot_id}", json=payload)
    
    lot = resp.json()
    print(f"After Removal: client_id={lot.get('client_id')}, acquereur='{lot.get('acquereur')}'")

    if lot.get("client_id") is None and (lot.get("acquereur") == "" or lot.get("acquereur") is None):
        print("SUCCESS: Client removed correctly.")
    else:
        print("FAILURE: Client was not removed or acquereur not cleared.")

if __name__ == "__main__":
    run()
