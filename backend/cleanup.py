import httpx
import sys

BASE_URL = "http://127.0.0.1:8001"

def run():
    # 1. Find and delete the test programme
    print("Finding 'Test Prog temp'...")
    resp = httpx.get(f"{BASE_URL}/programmes")
    if resp.status_code == 200:
        progs = resp.json()
        for p in progs:
            if p["nom"] == "Test Prog temp":
                print(f"Deleting programme {p['id']} ({p['nom']})...")
                del_resp = httpx.delete(f"{BASE_URL}/programmes/{p['id']}")
                if del_resp.status_code == 200:
                    print("Programme deleted.")
                else:
                    print(f"Failed to delete programme: {del_resp.text}")

    # 2. Find and delete the test client
    print("Finding 'TestClient TOTO'...")
    resp = httpx.get(f"{BASE_URL}/clients")
    if resp.status_code == 200:
        clients = resp.json()
        # The list endpoint might return different structure depending on backend
        # based on models.py inspection, it seems to return list[ClientRead]
        for c in clients:
            # ClientRead has last_name, first_name
            if c.get("last_name") == "TestClient" and c.get("first_name") == "TOTO":
                print(f"Deleting client {c['id']} ({c['last_name']} {c['first_name']})...")
                del_resp = httpx.delete(f"{BASE_URL}/clients/{c['id']}")
                if del_resp.status_code == 204 or del_resp.status_code == 200:
                    print("Client deleted.")
                else:
                    print(f"Failed to delete client: {del_resp.text}")

if __name__ == "__main__":
    run()
