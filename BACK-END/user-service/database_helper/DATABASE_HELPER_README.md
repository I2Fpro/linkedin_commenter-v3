# 🔧 Database Helper - Documentation Complète

Module utilitaire pour gérer la base de données utilisateurs **RÉELLE** avec chiffrement transparent.

---

## 🤖 CLAUDE : LISEZ CECI EN PREMIER !

> ⚠️ **RÈGLE ABSOLUE** : **TOUJOURS** exécuter les scripts via `docker exec linkedin_ai_user_service`
>
> **Commande la plus simple pour lister les utilisateurs :**
> ```bash
> # Sur Git Bash (Windows)
> cd d:\DEV\GIT\Ai_Commentary\BACK-END
> MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/list_users_simple.py
>
> # Sur PowerShell/CMD (Windows) ou Linux/Mac
> docker exec linkedin_ai_user_service python /app/list_users_simple.py
> ```
>
> **❌ JAMAIS** : `python list_users_simple.py` ou `python database_helper/list_users.py`
>
> **✅ TOUJOURS** : `docker exec linkedin_ai_user_service python /app/SCRIPT.py`
>
> **RAISON** : La base PostgreSQL utilise le hostname `postgres` qui n'existe que dans le réseau Docker.
>
> **NOTE GIT BASH** : Sur Git Bash Windows, le préfixe `MSYS_NO_PATHCONV=1` empêche la conversion automatique des chemins Unix en chemins Windows.

---

> ⚠️ **IMPORTANT POUR CLAUDE** : Ce module interagit avec la **base de données de production** via Docker.
> Les exemples et scripts utilisent les **vraies données utilisateurs**, pas des exemples fictifs.

---

## 📋 Table des Matières

- [⚡ Démarrage Rapide](#-démarrage-rapide)
- [🤖 Instructions pour Claude](#-instructions-pour-claude)
- [📚 Documentation Complète](#-documentation-complète)

---

# ⚡ Démarrage Rapide

## 🚀 Commandes Essentielles

> ⚠️ **IMPORTANT** : TOUTES les commandes ci-dessous DOIVENT être exécutées via `docker exec` depuis le conteneur `linkedin_ai_user_service`

### Vérifier que Docker est lancé (PREMIÈRE ÉTAPE OBLIGATOIRE)

```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END
docker-compose ps
```

Les services doivent afficher le statut `Up` et `(healthy)`.

### Lister les utilisateurs (version simple et rapide)

```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END

# Git Bash (Windows)
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/list_users_simple.py

# PowerShell/CMD (Windows) ou Linux/Mac
docker exec linkedin_ai_user_service python /app/list_users_simple.py
```

Ce script affiche tous les utilisateurs avec leurs détails et les statistiques par rôle.

### Lister les utilisateurs (version complète avec détection de doublons)

```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END

# Git Bash (Windows)
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/list_users.py

# PowerShell/CMD (Windows) ou Linux/Mac
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py
```

### Statistiques uniquement

```bash
# Git Bash (Windows)
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/list_users.py stats

# PowerShell/CMD (Windows) ou Linux/Mac
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py stats
```

### Détecter les doublons

```bash
# Git Bash (Windows)
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/list_users.py duplicates

# PowerShell/CMD (Windows) ou Linux/Mac
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py duplicates
```

---

# 🤖 Instructions pour Claude

> ⚠️ **ATTENTION CLAUDE** : Règles OBLIGATOIRES pour interagir avec la base de données.

## 🎯 Règles Importantes

### 1. Base de Données RÉELLE

- **TOUJOURS** considérer que vous travaillez avec la **base de données de PRODUCTION**
- Les scripts et commandes utilisent les **VRAIES données utilisateurs**
- **JAMAIS** supposer que ce sont des exemples fictifs
- Les utilisateurs actuels dans la base sont :
  - `isshia.inapogui@gmail.com` (MEDIUM) - ⚠️ DOUBLON (2 entrées)
  - `i2frl.test@gmail.com` (FREE) - ⚠️ DOUBLON (2 entrées)
  - `i2frl.pro@gmail.com` (PREMIUM) - ⚠️ DOUBLON (2 entrées)
  - `florianroullierlenoir@gmail.com` (MEDIUM)

### 2. Exécution via Docker OBLIGATOIRE

**TOUTES** les commandes Python qui accèdent à la base de données **DOIVENT** être exécutées via Docker :

```bash
# Format général
docker exec linkedin_ai_user_service python /app/SCRIPT.py

# Exemples concrets
docker exec linkedin_ai_user_service python /app/list_users_simple.py
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py
```

**POURQUOI ?**
- La base PostgreSQL utilise le hostname `postgres` défini dans docker-compose.yml
- Ce hostname n'est résolu que dans le réseau Docker interne
- Exécuter en dehors de Docker provoquera l'erreur : `could not translate host name "postgres" to address`
- La connexion PostgreSQL nécessite le réseau Docker pour communiquer entre conteneurs

**❌ CE QUI NE FONCTIONNE PAS :**
```bash
# ❌ Exécution directe sur Windows - NE FONCTIONNE PAS
python d:\DEV\GIT\Ai_Commentary\BACK-END\user-service\list_users_simple.py
# Erreur: could not translate host name "postgres" to address

# ❌ Exécution depuis le répertoire - NE FONCTIONNE PAS
cd d:\DEV\GIT\Ai_Commentary\BACK-END\user-service
python list_users_simple.py
# Erreur: could not translate host name "postgres" to address
```

**✅ CE QUI FONCTIONNE :**
```bash
# ✅ Sur Git Bash (Windows) - Ajouter MSYS_NO_PATHCONV=1
cd d:\DEV\GIT\Ai_Commentary\BACK-END
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/list_users_simple.py

# ✅ Sur PowerShell/CMD (Windows) ou Linux/Mac - Syntaxe normale
cd d:\DEV\GIT\Ai_Commentary\BACK-END
docker exec linkedin_ai_user_service python /app/list_users_simple.py
```

**NOTE SUR GIT BASH** : Git Bash sur Windows convertit automatiquement les chemins Unix (`/app/`) en chemins Windows (`D:/Program Files/Git/app/`). Le préfixe `MSYS_NO_PATHCONV=1` désactive cette conversion.

### 3. Localisation des Fichiers

**Depuis Windows (hôte)** :
```
d:\DEV\GIT\Ai_Commentary\BACK-END\user-service\database_helper\
```

**Dans le conteneur Docker** :
```
/app/database_helper/
```

Les fichiers sur l'hôte sont montés dans `/app/` du conteneur.

---

## 📝 Commandes Courantes

### Lister les utilisateurs réels

```bash
# Liste complète avec détails
cd d:\DEV\GIT\Ai_Commentary\BACK-END

# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/list_users.py

# PowerShell/CMD/Linux/Mac
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py
```

### Code Python personnalisé

```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END

# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python -c "
import sys
sys.path.insert(0, '/app/database_helper')
from database_helper import DatabaseHelper

helper = DatabaseHelper()

# Votre code ici...
users = helper.list_all_users()
for user in users:
    print(f'{user.email} - {user.role.value}')
"

# PowerShell/CMD/Linux/Mac (syntaxe identique sans MSYS_NO_PATHCONV=1)
```

---

## 🚫 Erreurs Courantes à Éviter

### ❌ ERREUR 1: Exécuter Python directement sur l'hôte

```bash
# ❌ NE PAS FAIRE
cd d:\DEV\GIT\Ai_Commentary\BACK-END
python database_helper/list_users.py
```

**Résultat** : `could not translate host name "postgres" to address`

**Solution** :
```bash
# ✅ CORRECT (Git Bash)
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/list_users.py

# ✅ CORRECT (PowerShell/CMD/Linux/Mac)
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py
```

### ❌ ERREUR 2: Oublier MSYS_NO_PATHCONV=1 sur Git Bash

```bash
# ❌ NE PAS FAIRE sur Git Bash
docker exec linkedin_ai_user_service python /app/list_users_simple.py
```

**Résultat** : `python: can't open file '/app/D:/Program Files/Git/app/list_users_simple.py'`

**Solution** :
```bash
# ✅ CORRECT sur Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/list_users_simple.py
```

### ❌ ERREUR 3: Utiliser des exemples fictifs

```python
# ❌ NE PAS FAIRE
user = helper.get_user_by_email("example@test.com")  # Cet utilisateur n'existe pas
```

**Solution** :
```python
# ✅ CORRECT - Utiliser les vrais emails
user = helper.get_user_by_email("isshia.inapogui@gmail.com")
```

### ❌ ERREUR 4: Créer des utilisateurs sans avertir

```python
# ❌ NE PAS FAIRE sans prévenir l'utilisateur
helper.create_user("new@test.com", "Test", RoleType.FREE)
```

**Solution** :
```python
# ✅ CORRECT - Toujours demander confirmation avant création
# Et prévenir que cela modifie la base de production
```

---

## 🔍 Workflow Recommandé

### Pour lister les utilisateurs :

1. Vérifier que Docker tourne : `docker-compose ps`
2. Exécuter avec la bonne syntaxe selon votre shell
3. Interpréter les résultats (ce sont les VRAIES données)

### Pour modifier la base :

1. **TOUJOURS** faire un backup ou dry-run d'abord
2. Demander confirmation à l'utilisateur
3. Exécuter via Docker avec la bonne syntaxe
4. Vérifier le résultat

### Pour rechercher un utilisateur :

1. Lister d'abord les utilisateurs pour voir les emails disponibles
2. Utiliser un email réel de la base
3. Ne pas supposer qu'un email existe

---

## 🎓 Exemples Concrets pour Claude

### Exemple 1: Lister les utilisateurs

**Question utilisateur** : "Montre-moi les utilisateurs"

**Réponse Claude** :
```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END

# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/list_users_simple.py

# PowerShell/CMD/Linux/Mac
docker exec linkedin_ai_user_service python /app/list_users_simple.py
```

### Exemple 2: Trouver un utilisateur spécifique

**Question utilisateur** : "Est-ce que isshia.inapogui@gmail.com existe ?"

**Réponse Claude** :
```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END

# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python -c "
import sys
sys.path.insert(0, '/app/database_helper')
from database_helper import DatabaseHelper

helper = DatabaseHelper()
user = helper.get_user_by_email('isshia.inapogui@gmail.com')

if user:
    print(f'✅ Utilisateur trouvé')
    print(f'   Email: {user.email}')
    print(f'   Nom: {user.name}')
    print(f'   Rôle: {user.role.value}')
    print(f'   ID: {user.id}')
else:
    print('❌ Utilisateur non trouvé')
"

# Sur PowerShell/CMD/Linux/Mac, même commande sans MSYS_NO_PATHCONV=1
```

### Exemple 3: Détecter les doublons

**Question utilisateur** : "Y a-t-il des doublons ?"

**Réponse Claude** :
```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END

# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/list_users.py duplicates

# PowerShell/CMD/Linux/Mac
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py duplicates
```

---

## ✅ Checklist avant chaque commande

- [ ] Docker est-il lancé ? (`docker-compose ps`)
- [ ] La commande utilise-t-elle `docker exec` ?
- [ ] Le chemin est-il `/app/database_helper/` (dans le conteneur) ?
- [ ] Sur Git Bash Windows : ai-je ajouté `MSYS_NO_PATHCONV=1` ?
- [ ] Si création/modification : l'utilisateur est-il prévenu ?
- [ ] Les emails utilisés existent-ils vraiment dans la base ?

---

## 🎯 Résumé pour Claude

**À RETENIR** :
1. ✅ Base de données RÉELLE = vraies données
2. ✅ Toujours utiliser `docker exec linkedin_ai_user_service`
3. ✅ Sur Git Bash Windows : ajouter `MSYS_NO_PATHCONV=1` devant
4. ✅ Sur PowerShell/CMD/Linux/Mac : syntaxe normale
5. ✅ Chemins : `/app/database_helper/` dans Docker, `d:\DEV\GIT\Ai_Commentary\BACK-END\user-service\database_helper\` sur Windows
6. ✅ Demander confirmation avant modifications
7. ✅ Utiliser les emails réels : `isshia.inapogui@gmail.com`, `i2frl.pro@gmail.com`, etc.

---

# 📚 Documentation Complète

## 🚀 Installation

### Prérequis

```bash
pip install tabulate
```

Le package `tabulate` est déjà inclus dans `requirements.txt` du conteneur Docker.

### Vérifier que Docker est lancé

```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END
docker-compose ps
```

Les services doivent être UP (postgres, redis, ai-service, user-service).

---

## 📝 Scripts Utilitaires

### 0. `list_users_simple.py` - Script Simple et Rapide ⭐ RECOMMANDÉ

**Le plus simple à utiliser pour lister rapidement tous les utilisateurs.**

```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END

# Git Bash (Windows)
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/list_users_simple.py

# PowerShell/CMD (Windows) ou Linux/Mac
docker exec linkedin_ai_user_service python /app/list_users_simple.py
```

**Affiche :**
- Liste complète de tous les utilisateurs avec détails
- Email, nom, ID, rôle, statut actif, Google ID, dates de création/mise à jour
- Statistiques par rôle (FREE, MEDIUM, PREMIUM)

**Avantages :**
- ✅ Pas de paramètres nécessaires
- ✅ Affichage formaté et lisible
- ✅ Gère automatiquement l'encodage UTF-8 sur Windows
- ✅ Parfait pour un aperçu rapide de la base

**Note :** Ce script est situé à la racine de `/app/` dans le conteneur pour un accès facile.

### 1. `list_users.py` - Lister les utilisateurs avec Options Avancées

**Version complète avec détection de doublons et rapports de santé.**

```bash
cd d:\DEV\GIT\Ai_Commentary\BACK-END

# Liste complète avec tous les détails + doublons + santé de la base
# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/list_users.py

# PowerShell/CMD/Linux/Mac
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py

# Statistiques uniquement
# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/list_users.py stats

# PowerShell/CMD/Linux/Mac
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py stats

# Détecter les doublons uniquement
# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/list_users.py duplicates

# PowerShell/CMD/Linux/Mac
docker exec linkedin_ai_user_service python /app/database_helper/list_users.py duplicates
```

**Affiche en plus de list_users_simple.py :**
- Détection automatique des doublons (email et google_id)
- Rapport de santé de la base de données
- Vérification des enregistrements orphelins
- Validation des emails

### 2. `examples.py` - Exemples d'utilisation

```bash
# Exemples de base
# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/database_helper/examples.py

# PowerShell/CMD/Linux/Mac
docker exec linkedin_ai_user_service python /app/database_helper/examples.py

# Nettoyer les doublons (interactif) - Ajouter -it pour l'interaction
# Git Bash
MSYS_NO_PATHCONV=1 docker exec -it linkedin_ai_user_service python /app/database_helper/examples.py cleanup

# PowerShell/CMD/Linux/Mac
docker exec -it linkedin_ai_user_service python /app/database_helper/examples.py cleanup
```

### 3. Code Python Direct (Avancé)

**Depuis le conteneur Docker uniquement** :

```bash
# Git Bash
MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python -c "
import sys
sys.path.insert(0, '/app/database_helper')
from database_helper import DatabaseHelper, print_user_table

helper = DatabaseHelper()

# Lister tous les utilisateurs RÉELS
users = helper.list_all_users()
print_user_table(users)

# Statistiques RÉELLES
stats = helper.get_user_stats()
print(stats)
"

# PowerShell/CMD/Linux/Mac (même commande sans MSYS_NO_PATHCONV=1)
```

---

## 🎯 Fonctionnalités

### ✅ Gestion des Utilisateurs

- **Créer** un ou plusieurs utilisateurs
- **Lire** les données déchiffrées automatiquement
- **Mettre à jour** le rôle ou le statut
- **Supprimer** avec confirmation
- **Rechercher** par email ou ID

### 🔍 Détection de Doublons

- Détecter les doublons d'**email**
- Détecter les doublons de **google_id**
- Afficher les détails de chaque doublon

### 🧹 Nettoyage Automatique

- **3 stratégies** de nettoyage :
  - `keep_newest` : Garde le plus récent
  - `keep_oldest` : Garde le plus ancien
  - `keep_most_active` : Garde le plus utilisé
- **Mode dry-run** pour simuler avant suppression
- **Fusion automatique** des historiques d'usage

### 🔐 Validation et Sécurité

- Vérification de l'**intégrité du chiffrement**
- Détection des **enregistrements orphelins**
- Validation du **format des emails**
- **Rapport de santé** complet de la base

### 📊 Statistiques et Reporting

- Statistiques par **rôle**
- Comptage **actifs/inactifs**
- Historique d'**utilisation** par utilisateur
- Affichage formaté en **tableaux**

---

## 📖 API Complète du DatabaseHelper

### Classe `DatabaseHelper`

#### Création d'Utilisateurs

```python
create_user(email, name=None, role=RoleType.FREE, google_id=None, is_active=True)
# Retourne: (success: bool, message: str, user: Optional[User])

create_users_batch(users_data: List[Dict])
# Retourne: (created: int, skipped: int, messages: List[str])
```

#### Lecture et Recherche

```python
get_user_by_email(email: str) -> Optional[User]

get_user_by_id(user_id: str) -> Optional[User]

list_all_users(show_inactive=False, role_filter=None) -> List[User]

list_users_by_role(role: RoleType) -> List[User]

get_user_stats() -> Dict[str, Any]

get_user_usage_history(email_or_id: str, days=30) -> Tuple[User, List[UsageLog]]
```

#### Mise à Jour et Suppression

```python
update_user_role(email_or_id: str, new_role: RoleType) -> Tuple[bool, str]

toggle_user_status(email_or_id: str, is_active: bool) -> Tuple[bool, str]

delete_user(email_or_id: str, force=False) -> Tuple[bool, str]
```

#### Détection de Doublons

```python
find_duplicate_emails() -> List[Dict[str, Any]]

find_duplicate_google_ids() -> List[Dict[str, Any]]

find_all_duplicates() -> Dict[str, List[Dict[str, Any]]]
```

#### Nettoyage

```python
cleanup_duplicates(strategy='keep_newest', dry_run=True) -> Tuple[int, List[str]]

remove_duplicate(email_or_id: str, confirm=False) -> Tuple[bool, str]
```

#### Validation et Santé

```python
verify_encryption_integrity() -> Tuple[bool, List[str]]

validate_database_health() -> Dict[str, Any]

check_orphaned_records() -> Dict[str, List[str]]

generate_health_report() -> str
```

### Fonctions Utilitaires d'Affichage

```python
print_user_table(users: List[User], show_google_id=False)

print_stats_summary(stats: Dict[str, Any])

print_duplicates_report(duplicates: Dict[str, List[Dict[str, Any]]])

print_usage_history(user: User, logs: List[UsageLog])
```

---

## 🔐 Sécurité et Chiffrement

Le module utilise le **chiffrement transparent** via `EncryptedString` :

- Les champs **email**, **name**, et **google_id** sont automatiquement chiffrés
- Le chiffrement utilise **Fernet (AES-128)** avec la clé du `.env`
- Le déchiffrement est automatique lors de la lecture
- Les comparaisons (`==`) fonctionnent même sur les champs chiffrés

**Important:**
- La clé `ENCRYPTION_KEY` dans `.env` est **critique**
- Si la clé est perdue, les données sont **irrécupérables**
- Ne **jamais** committer la clé dans Git

---

## ⚠️ Bonnes Pratiques

### Avant de Supprimer

```python
# Toujours faire un dry-run d'abord
deleted, messages = helper.cleanup_duplicates(strategy='keep_newest', dry_run=True)
for msg in messages:
    print(msg)

# Vérifier les résultats, puis exécuter
if input("Continuer? (y/N): ") == 'y':
    deleted, messages = helper.cleanup_duplicates(strategy='keep_newest', dry_run=False)
```

### Avant de Migrer en Masse

```python
# Vérifier la santé de la base
report = helper.generate_health_report()
print(report)

# Corriger les problèmes détectés
duplicates = helper.find_all_duplicates()
if duplicates:
    print("⚠️  Nettoyer les doublons d'abord!")
```

### Backup Régulier

```bash
# Avant toute opération destructive
pg_dump linkedin_ai_db > backup_$(date +%Y%m%d).sql
```

---

## 🐛 Résolution de Problèmes

### PostgreSQL inaccessible

**Symptôme** : `could not translate host name "postgres"`

**Solution** :
1. Vérifier Docker : `docker-compose ps`
2. Utiliser `docker exec` au lieu d'exécution directe
3. Redémarrer si nécessaire : `docker-compose restart`

### Conversion de chemin Git Bash

**Symptôme** : `python: can't open file '/app/D:/Program Files/Git/app/...'`

**Solution** :
- Ajouter `MSYS_NO_PATHCONV=1` devant la commande sur Git Bash
- Ou utiliser PowerShell/CMD à la place

### Utilisateur Non Trouvé

**Symptôme** : `❌ Utilisateur non trouvé`

**Solution** :
1. Lister d'abord tous les utilisateurs
2. Vérifier l'orthographe exacte de l'email (sensible à la casse)
3. S'assurer que l'utilisateur existe vraiment

### Erreur d'Import

**Symptôme** : `ModuleNotFoundError: No module named 'database_helper'`

**Solution** :
- Ajouter `sys.path.insert(0, '/app/database_helper')` au début du script
- Ou utiliser les scripts wrapper existants (`list_users.py`, `examples.py`)

### Erreur de Chiffrement

```python
# Vérifier l'intégrité
encryption_ok, messages = helper.verify_encryption_integrity()
for msg in messages:
    print(msg)
```

---

## 📝 Notes

- **Toutes les opérations** respectent les contraintes de la base (CASCADE, etc.)
- Les **suppressions** suppriment automatiquement les subscriptions et usage_logs liés
- Le **nettoyage de doublons** fusionne les historiques d'usage
- Les **fonctions de lecture** expunge les objets pour éviter les problèmes de session

---

## 🤝 Contribution

Pour ajouter de nouvelles fonctionnalités, modifier `database_helper.py` et mettre à jour ce README.

**Structure recommandée:**
1. Ajouter la fonction à la classe `DatabaseHelper`
2. Documenter avec docstring complète
3. Ajouter un exemple dans `examples.py`
4. Mettre à jour ce README avec l'exemple

---

## 📄 Licence

Ce module fait partie du projet LinkedIn AI Commenter.
