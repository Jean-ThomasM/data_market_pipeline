# Procédure — Installation Docker + Docker Compose (propre GCP)

## 1. Mise à jour minimale

```bash
sudo apt update
```

---

## 2. Installer les prérequis

```bash
sudo apt install -y ca-certificates curl gnupg
```

---

## 3. Ajouter la clé officielle Docker

```bash
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/debian/gpg \
| sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

---

## 4. Ajouter le dépôt Docker (Debian Bookworm)

```bash
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
bookworm stable" \
| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

---

## 5. Installer Docker + Compose (versions récentes)

```bash
sudo apt update

sudo apt install -y \
docker-ce \
docker-ce-cli \
containerd.io \
docker-buildx-plugin \
docker-compose-plugin
```

---

## 6. Démarrer Docker

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

---

## 7. (Optionnel mais recommandé) éviter sudo

```bash
sudo usermod -aG docker $USER
```

👉 Puis :

* se déconnecter / reconnecter SSH

---

# Tests de validation

## Test 1 — Version Docker

```bash
docker --version
```

👉 attendu :

```
Docker version XX.X.X
```

---

## Test 2 — Version Docker Compose

```bash
docker compose version
```

👉 attendu :

```
Docker Compose version vX.X.X
```

---

## Test 3 — Test conteneur

```bash
docker run hello-world
```

👉 attendu :

```
Hello from Docker!
```

---

## Test 4 — Service actif

```bash
systemctl status docker --no-pager
```

👉 attendu :

```
active (running)
```

---

# Résultat final

✔ Docker installé proprement depuis dépôt officiel
✔ Docker Compose moderne (`docker compose`, pas legacy)
✔ Compatible images récentes (n8n, etc.)
✔ Stable sur GCP
