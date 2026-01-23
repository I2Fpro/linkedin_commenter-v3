# Historique des Changements de Rôle

Ce système permet de tracer tous les changements de rôle des utilisateurs dans une table d'audit dédiée.

## Table `role_change_history`

### Structure

| Colonne      | Type                     | Description                                           |
|--------------|--------------------------|-------------------------------------------------------|
| `id`         | UUID                     | Identifiant unique de l'entrée                        |
| `user_id`    | UUID                     | Référence vers l'utilisateur (clé étrangère)          |
| `old_role`   | ENUM(RoleType)           | Ancien rôle (NULL si création initiale)               |
| `new_role`   | ENUM(RoleType)           | Nouveau rôle                                          |
| `changed_at` | TIMESTAMP WITH TIME ZONE | Date et heure du changement                           |
| `changed_by` | VARCHAR(255)             | Email ou ID de l'admin qui a fait le changement       |
| `reason`     | TEXT                     | Raison du changement                                  |
| `meta_data`  | JSON                     | Données supplémentaires (optionnel)                   |

### Index

- Index primaire sur `id`
- Index sur `user_id`
- Index sur `changed_at`
- Index composite sur `(user_id, changed_at)` pour les requêtes fréquentes

## Utilisation

### 1. Enregistrer le rôle initial d'un nouvel utilisateur

```python
from utils.role_manager import RoleManager

# Après avoir créé un utilisateur
new_user = User(
    email="user@example.com",
    name="John Doe",
    role=RoleType.FREE
)
db.add(new_user)
db.flush()

# Enregistrer le rôle initial dans l'historique
RoleManager.record_initial_role(
    db=db,
    user=new_user,
    reason="Inscription via Google OAuth",
    meta_data={"source": "google_oauth"}
)

db.commit()
```

### 2. Changer le rôle d'un utilisateur

```python
from utils.role_manager import RoleManager

# Changer le rôle d'un utilisateur existant
try:
    RoleManager.change_user_role(
        db=db,
        user=current_user,
        new_role=RoleType.PREMIUM,
        changed_by="admin@example.com",
        reason="Upgrade suite à l'achat d'un abonnement",
        meta_data={
            "payment_id": "pay_123456",
            "plan": "monthly"
        }
    )
    db.commit()
except ValueError as e:
    # Le rôle est déjà le même
    print(f"Erreur: {e}")
```

### 3. Récupérer l'historique des changements

```python
from utils.role_manager import RoleManager

# Récupérer tout l'historique d'un utilisateur
history = RoleManager.get_user_role_history(
    db=db,
    user_id=user.id
)

for entry in history:
    print(f"{entry.changed_at}: {entry.old_role} -> {entry.new_role}")
    print(f"  Par: {entry.changed_by}")
    print(f"  Raison: {entry.reason}")

# Limiter à 10 entrées
recent_history = RoleManager.get_user_role_history(
    db=db,
    user_id=user.id,
    limit=10
)
```

### 4. Obtenir un résumé des changements

```python
from utils.role_manager import RoleManager

summary = RoleManager.get_role_change_summary(db=db, user_id=user.id)

print(f"Total de changements: {summary['total_changes']}")
print(f"Rôle initial: {summary['initial_role']}")
print(f"Rôle actuel: {summary['current_role']}")
print(f"Dernier changement: {summary['last_change_date']}")

# Détails de chaque changement
for change in summary['changes']:
    print(f"{change['date']}: {change['from']} -> {change['to']}")
    print(f"  Raison: {change['reason']}")
```

## Requêtes SQL utiles

### Voir tous les changements de rôle d'un utilisateur

```sql
SELECT
    u.email,
    rch.old_role,
    rch.new_role,
    rch.changed_at,
    rch.changed_by,
    rch.reason
FROM role_change_history rch
JOIN users u ON u.id = rch.user_id
WHERE u.email = 'user@example.com'
ORDER BY rch.changed_at DESC;
```

### Voir tous les utilisateurs qui sont passés de FREE à PREMIUM

```sql
SELECT
    u.email,
    rch.changed_at,
    rch.changed_by,
    rch.reason
FROM role_change_history rch
JOIN users u ON u.id = rch.user_id
WHERE rch.old_role = 'FREE'
  AND rch.new_role = 'PREMIUM'
ORDER BY rch.changed_at DESC;
```

### Statistiques sur les changements de rôle

```sql
SELECT
    old_role,
    new_role,
    COUNT(*) as total_changes
FROM role_change_history
WHERE old_role IS NOT NULL  -- Exclure les créations initiales
GROUP BY old_role, new_role
ORDER BY total_changes DESC;
```

### Voir les utilisateurs ayant changé de rôle récemment

```sql
SELECT
    u.email,
    rch.old_role,
    rch.new_role,
    rch.changed_at,
    rch.reason
FROM role_change_history rch
JOIN users u ON u.id = rch.user_id
WHERE rch.changed_at > NOW() - INTERVAL '7 days'
  AND rch.old_role IS NOT NULL
ORDER BY rch.changed_at DESC;
```

## Migration

La migration Alembic `003_add_role_change_history.py` crée automatiquement la table et ses index.

Pour appliquer la migration :

```bash
docker compose exec user-service alembic upgrade head
```

Pour annuler la migration (⚠️ supprime toutes les données d'historique) :

```bash
docker compose exec user-service alembic downgrade -1
```

## Intégration automatique

Le système est automatiquement intégré dans :

1. **Route PUT /profile** (routers/users.py:51-82) : Enregistre automatiquement les changements de rôle lors de la mise à jour du profil
2. **Script create_initial_users.py** : Enregistre le rôle initial lors de la création d'utilisateurs

## Notes importantes

- La contrainte `ON DELETE CASCADE` supprime automatiquement l'historique quand un utilisateur est supprimé
- Le champ `old_role` est `NULL` pour les entrées de création initiale
- Tous les changements sont horodatés avec un fuseau horaire (UTC par défaut)
- Les métadonnées JSON permettent de stocker des informations contextuelles supplémentaires

## Exemple complet

```python
from models import User, RoleType
from utils.role_manager import RoleManager
from database import get_db

db = next(get_db())

# 1. Créer un utilisateur
user = User(
    email="example@test.com",
    name="Test User",
    role=RoleType.FREE
)
db.add(user)
db.flush()

# 2. Enregistrer le rôle initial
RoleManager.record_initial_role(db, user, reason="Création compte")

# 3. Passer à MEDIUM après 1 mois
RoleManager.change_user_role(
    db, user, RoleType.MEDIUM,
    changed_by="admin@example.com",
    reason="Upgrade mensuel",
    meta_data={"payment": "stripe_123"}
)

# 4. Passer à PREMIUM après 3 mois
RoleManager.change_user_role(
    db, user, RoleType.PREMIUM,
    changed_by="admin@example.com",
    reason="Upgrade annuel"
)

db.commit()

# 5. Voir l'historique
summary = RoleManager.get_role_change_summary(db, user.id)
print(f"Parcours: {summary['initial_role']} -> {summary['current_role']}")
print(f"Total changements: {summary['total_changes']}")
```
