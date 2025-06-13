# MASTERCAMP
# Cloner un dépôt
git clone https://github.com/utilisateur/nom-du-repo.git
cd nom-du-repo

# Vérifier l’état du projet
git status

# Récupérer les dernières modifications du dépôt distant
git pull origin main

# Ajouter tous les fichiers modifiés
git add .

# Faire un commit avec un message clair
git commit -m "Message de commit"

# Pousser les changements sur la branche principale
git push origin main

# Créer une nouvelle branche pour une fonctionnalité ou un correctif
git checkout -b nom-de-ta-branche

# Pousser cette nouvelle branche
git push origin nom-de-ta-branche

# Changer de branche
git checkout nom-de-la-branche

# Fusionner une autre branche dans la branche actuelle
git merge nom-de-la-branche-a-fusionner

# Récupérer toutes les branches distantes
git fetch

# Supprimer une branche locale
git branch -d nom-de-la-branche

# Supprimer une branche distante
git push origin --delete nom-de-la-branche