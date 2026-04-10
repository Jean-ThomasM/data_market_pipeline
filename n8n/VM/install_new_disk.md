# 📦 Mémo — Ajouter et monter un disque (DD) sur une VM Linux + Docker

## 🎯 Objectif

Ajouter un disque, le monter proprement, et l’utiliser pour stocker des données (ex : volumes Docker n8n / Postgres).

---

# 1️⃣ Vérifier que le disque est détecté

```bash
lsblk
```

Exemple de sortie :

```bash
sda    8:0    0   20G  0 disk
└─sda1 8:1    0   20G  0 part /

sdb    8:16   0   50G  0 disk   <-- nouveau disque
```

---

# 2️⃣ Créer une partition

```bash
sudo fdisk /dev/sdb
```

Commandes à entrer dans fdisk :

```bash
n    # new partition
p    # primary
1    # partition 1
Enter
Enter
w    # write
```

---

# 3️⃣ Formater le disque

```bash
sudo mkfs.ext4 /dev/sdb1
```

---

# 4️⃣ Créer un point de montage

```bash
sudo mkdir -p /mnt/data
```

---

# 5️⃣ Monter le disque

```bash
sudo mount /dev/sdb1 /mnt/data
```

Vérifier :

```bash
df -h
```

---

# 6️⃣ Monter automatiquement au démarrage

Récupérer l’UUID :

```bash
sudo blkid
```

Exemple :

```bash
/dev/sdb1: UUID="1234-5678-ABCD" TYPE="ext4"
```

Éditer le fichier :

```bash
sudo nano /etc/fstab
```

Ajouter :

```bash
UUID=1234-5678-ABCD /mnt/data ext4 defaults,nofail 0 2
```

Tester sans reboot :

```bash
sudo mount -a
```

---

# 7️⃣ Donner les droits (important pour Docker)

```bash
sudo chown -R $USER:$USER /mnt/data
```

---

# 8️⃣ Créer les dossiers pour n8n / Postgres

```bash
mkdir -p /mnt/data/n8n
mkdir -p /mnt/data/postgres
mkdir -p /mnt/data/files
```

---

# 9️⃣ Déplacer des données existantes

### Exemple : déplacer n8n

```bash
sudo systemctl stop docker

mv ~/n8n /mnt/data/n8n
```

OU si volume existant :

```bash
sudo rsync -avh ~/n8n/ /mnt/data/n8n/
```

---

# 🔟 Adapter docker-compose

Exemple :

```yaml
volumes:
  - /mnt/data/n8n:/home/node/.n8n
  - /mnt/data/postgres:/var/lib/postgresql/data
```

---

# 1️⃣1️⃣ Relancer Docker

```bash
docker compose down
docker compose up -d
```

---

# 1️⃣2️⃣ Vérifications

```bash
docker ps
```

```bash
docker logs n8n
```

---

# ⚠️ Points d’attention

* Toujours utiliser `/mnt/data` (ou équivalent) → évite de remplir le disque système
* Vérifier les droits (`chown`)
* Toujours tester `/etc/fstab` avec `mount -a`
* Utiliser `rsync` plutôt que `mv` si données sensibles

---

# ✅ Résultat

* Disque monté automatiquement
* Données persistantes sécurisées
* Docker utilise le bon stockage

---
