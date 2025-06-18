# MASTERCAMP
##############################
# 🛠️ 1. Récupérer le projet #
##############################

# Cloner un dépôt pour la première fois
git clone https://github.com/utilisateur/nom-du-repo.git
cd nom-du-repo

# Vérifier l’état actuel du projet
git status

# Récupérer les dernières modifications du dépôt distant (depuis la branche main)
git pull origin main

# Récupérer toutes les branches distantes
git fetch

# Changer de branche (si besoin)
git checkout nom-de-la-branche


#############################################
# ✏️ 2. Modifier le projet et pousser du code #
#############################################

# Ajouter tous les fichiers modifiés
# (ou mettre un nom de fichier à la place du point pour cibler un fichier)
git add .

# Faire un commit avec un message clair
git commit -m "Message de commit"

# Pousser les changements sur la branche principale (main)
git push origin main

# Créer une nouvelle branche pour une fonctionnalité ou un correctif
git checkout -b nom-de-ta-branche

# Pousser cette nouvelle branche
git push origin nom-de-ta-branche

# Fusionner une autre branche dans la branche actuelle
git merge nom-de-la-branche-a-fusionner

# Supprimer une branche locale
git branch -d nom-de-la-branche

# Supprimer une branche distante
git push origin --delete nom-de-la-branche