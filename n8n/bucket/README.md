# bucket `n8n-bucket`

## GCP

Créer une VM avec ces paramètres :
* Name : n8n-bucket
* Region : europe-west9 (Paris)

## Permissions

Va dans Cloud Storage → Buckets
Clique sur ton bucket
Onglet Permissions
Grant access
Dans New principals, colle : 888542975615-compute@developer.gserviceaccount.com (à modifier)

Dans Select a role, choisis :
Storage Legacy Bucket Owner
Storage Legacy Bucket Reader
Storage Object User
Storage Object Viewer