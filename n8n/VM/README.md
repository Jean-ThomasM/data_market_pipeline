# VM `n8n-vm-small`

## GCP

Créer une VM avec ces paramètres :
* Name : n8n-vm-small
* Region : europe-west9 (Paris)
* Machine types : E2-small

### augmentation du disque

Il faut ajouter un disque supplémentaire de 10Go.
Monter ce deuxième DD afin d'avoir quelque chose comme :
```
df -h
Filesystem      Size  Used Avail Use% Mounted on
udev            977M     0  977M   0% /dev
tmpfs           198M  768K  197M   1% /run
/dev/sdb1       9.7G  5.8G  3.4G  64% /
tmpfs           989M     0  989M   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
/dev/sdb15      124M   12M  113M  10% /boot/efi
tmpfs           198M     0  198M   0% /run/user/1000
/dev/sda        9.8G  3.3G  6.0G  36% /mnt/data
```

## Docker

Lire `install_docker.md`.