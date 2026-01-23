# Documentation du Chiffrement des Données

## Vue d'ensemble

Ce système utilise le chiffrement symétrique Fernet (basé sur AES) pour protéger les données sensibles des utilisateurs stockées en base de données PostgreSQL.

### Données chiffrées

Les colonnes suivantes de la table `users` sont automatiquement chiffrées :
- `email` : Adresse email de l'utilisateur
- `name` : Nom de l'utilisateur
- `google_id` : Identifiant Google OAuth

## Configuration

### 1. Clé de chiffrement

La clé de chiffrement est définie dans le fichier `.env` :

```bash
ENCRYPTION_KEY=4RoGN2Dhep0x04eL1lnEUzbAPzTGW2WgGKpCQ3P/7Pc=
```

**⚠️ IMPORTANT:**
- Ne **JAMAIS** commiter cette clé dans Git
- Garder cette clé en lieu sûr (gestionnaire de secrets, vault, etc.)
- Si vous perdez cette clé, les données chiffrées seront **définitivement** perdues
- Utiliser la même clé sur tous les environnements qui partagent la même base de données

### 2. Générer une nouvelle clé

Pour générer une nouvelle clé de chiffrement :

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Ou utilisez le module fourni :

```bash
cd /app
python -c "from utils.encryption import generate_encryption_key; print(generate_encryption_key())"
```

## Installation

### 1. Appliquer la migration

La migration modifie la taille des colonnes pour accueillir les données chiffrées (255 → 512 caractères) :

```bash
cd /app
alembic upgrade head
```

### 2. Chiffrer les données existantes

Si vous avez déjà des données en production, vous devez les chiffrer manuellement.

**⚠️ AVANT DE COMMENCER:**
1. Faites une sauvegarde complète de votre base de données
2. Arrêtez tous les services utilisant la base de données
3. Testez d'abord en mode `--dry-run`

```bash
# Test sans modification (recommandé)
cd /app
python scripts/encrypt_existing_data.py --dry-run

# Chiffrement réel
python scripts/encrypt_existing_data.py

# Vérification après chiffrement
python scripts/encrypt_existing_data.py --verify
```

## Utilisation

### Dans les modèles SQLAlchemy

Le chiffrement est **automatique** grâce au type personnalisé `EncryptedString` :

```python
from utils.encrypted_types import EncryptedString
from sqlalchemy import Column
from database import Base

class User(Base):
    __tablename__ = "users"

    # Colonne chiffrée automatiquement
    email = Column(EncryptedString(512), unique=True, nullable=False)
```

### Utilisation directe

Si vous avez besoin de chiffrer/déchiffrer manuellement :

```python
from utils.encryption import encrypt_field, decrypt_field

# Chiffrer
encrypted_data = encrypt_field("données sensibles")

# Déchiffrer
original_data = decrypt_field(encrypted_data)
```

### Dans les requêtes

Les données sont **automatiquement** chiffrées/déchiffrées par SQLAlchemy :

```python
from database import get_db
from models import User

db = next(get_db())

# Création d'un utilisateur (chiffrement automatique)
user = User(
    email="user@example.com",  # Sera chiffré automatiquement
    name="John Doe"            # Sera chiffré automatiquement
)
db.add(user)
db.commit()

# Lecture (déchiffrement automatique)
user = db.query(User).filter(User.email == "user@example.com").first()
print(user.email)  # Affiche "user@example.com" (déchiffré automatiquement)
```

## Architecture

### Composants

1. **`utils/encryption.py`**
   - Gestionnaire de chiffrement/déchiffrement
   - Utilise Fernet (AES-128 en mode CBC)
   - Gère la clé depuis les variables d'environnement

2. **`utils/encrypted_types.py`**
   - Type SQLAlchemy personnalisé `EncryptedString`
   - Chiffre automatiquement avant l'insertion
   - Déchiffre automatiquement lors de la lecture

3. **`models.py`**
   - Modèles SQLAlchemy utilisant `EncryptedString`

4. **`scripts/encrypt_existing_data.py`**
   - Script de migration pour chiffrer les données existantes
   - Modes dry-run et vérification

### Flux de données

```
Application → SQLAlchemy → EncryptedString → Fernet → PostgreSQL
    ↓                                                       ↑
Données claires                                    Données chiffrées
    ↓                                                       ↑
Lecture ← SQLAlchemy ← EncryptedString ← Fernet ← PostgreSQL
```

## Sécurité

### Bonnes pratiques

1. **Gestion de la clé**
   - Stocker `ENCRYPTION_KEY` dans un gestionnaire de secrets sécurisé
   - Ne jamais la commiter dans Git
   - Rotation régulière (voir section Rotation de clé)

2. **Sauvegarde**
   - Sauvegarder la clé séparément de la base de données
   - Tester régulièrement les restaurations

3. **Accès**
   - Limiter l'accès aux variables d'environnement
   - Logs : éviter de logger les données déchiffrées

### Limitations

- Le chiffrement protège les données **au repos** (dans la base)
- Les données sont **déchiffrées en mémoire** lors de l'utilisation
- Ce n'est **pas** du chiffrement de bout en bout
- Les recherches sur colonnes chiffrées sont plus lentes

### Recherche dans les colonnes chiffrées

⚠️ **Limitation importante** : Vous ne pouvez pas faire de recherches SQL directes sur les données chiffrées.

```python
# ❌ NE FONCTIONNE PAS
users = db.query(User).filter(User.email.like("%example.com")).all()

# ✅ Solution : Rechercher par correspondance exacte (l'égalité fonctionne)
user = db.query(User).filter(User.email == "user@example.com").first()

# ✅ Ou déchiffrer toutes les données en Python (moins performant)
all_users = db.query(User).all()
filtered_users = [u for u in all_users if "example.com" in u.email]
```

## Rotation de clé

Pour changer la clé de chiffrement (rotation de sécurité) :

1. **Sauvegarder la base de données**
2. **Déchiffrer avec l'ancienne clé** → Exporter en clair
3. **Générer une nouvelle clé**
4. **Mettre à jour `ENCRYPTION_KEY`** dans `.env`
5. **Re-chiffrer avec la nouvelle clé**

**Note**: Un script automatisé de rotation sera développé dans une version future.

## Dépannage

### Erreur : "ENCRYPTION_KEY n'est pas définie"

```bash
# Vérifier que le .env est chargé
cd /app
python -c "import os; from dotenv import load_dotenv; load_dotenv('../.env'); print(os.getenv('ENCRYPTION_KEY'))"
```

### Erreur : "La clé ENCRYPTION_KEY n'est pas valide"

La clé doit être une clé Fernet valide (44 caractères en base64). Générez-en une nouvelle :

```bash
python -c "from utils.encryption import generate_encryption_key; print(generate_encryption_key())"
```

### Les données apparaissent chiffrées dans l'application

Vérifiez que :
1. Le modèle utilise bien `EncryptedString`
2. La même clé est utilisée pour chiffrer et déchiffrer
3. Les migrations ont été appliquées

### Performance dégradée

Le chiffrement/déchiffrement a un coût :
- Utiliser des index sur les colonnes fréquemment recherchées
- Éviter de déchiffrer de grandes quantités de données
- Mettre en cache les résultats si possible

## Tests

Pour tester le module de chiffrement :

```bash
cd /app
python utils/encryption.py
```

Sortie attendue :
```
Test du module de chiffrement/déchiffrement
==================================================
Données originales: Données sensibles à protéger
Données chiffrées: gAAAAABl...
Données déchiffrées: Données sensibles à protéger

✓ Test réussi!
```

## Support

Pour toute question ou problème :
1. Vérifier cette documentation
2. Consulter les logs de l'application
3. Contacter l'équipe DevSecOps

---

**Dernière mise à jour** : 2025-10-15
**Version** : 1.0.0
