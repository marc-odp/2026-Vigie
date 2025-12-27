# Vigie - Indivision Manager

Vigie est une application de gestion comptable pour les biens immobiliers en indivision. Elle permet de suivre les revenus (loyers), les dépenses (frais, travaux) et de calculer automatiquement la répartition entre les propriétaires selon leurs quote-parts.

## Fonctionnalités Clés

- **Tableau de Bord** : Vue globale de la santé financière de l'indivision.
- **Journal des Opérations** : Saisie et suivi des entrées et sorties d'argent.
- **Matrice de Répartition** : Calcul automatique des soldes nets par propriétaire.
- **Gestion des Quote-Parts** : Support pour les structures de propriété complexes et évolutives.
- **Multi-Comptes** : Gestion de plusieurs comptes bancaires (courant, épargne, etc.).

## Installation

L'application utilise [uv](https://github.com/astral-sh/uv) pour la gestion des dépendances.

```bash
git clone https://github.com/votre-compte/vigie.git
cd vigie
uv sync
```

## Configuration

1. Copiez le fichier d'exemple pour les variables d'environnement :
   ```bash
   cp .env.example .env
   ```
2. Modifiez le fichier `.env` avec vos paramètres.

## Développement avec WSL (Windows Subsystem for Linux)

Si vous utilisez WSL2, voici quelques recommandations pour une expérience optimale :

- **Performance** : Clonez le projet dans le système de fichiers Linux (ex: `~/dev/vigie`) plutôt que dans `/mnt/c/`. La vitesse de lecture/écriture et le rafraîchissement automatique (hot-reload) de NiceGUI fonctionneront beaucoup mieux.
- **Accès Navigateur** : WSL2 gère normalement le transfert de port automatique. Vous pouvez accéder à l'app via `http://localhost:8080` sur votre Windows habituel.
- **Installation de uv** : Installez la version Linux de `uv` dans votre terminal WSL :
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## Utilisation

Pour lancer l'application :

```bash
# Via script (Linux/WSL)
chmod +x start.sh
./start.sh

# Ou manuellement
uv run python -m app.main
```

L'application est accessible sur `http://localhost:8080`.

**Identifiants par défaut (au premier lancement) :**
- Email : `admin@vigie.local`
- Mot de passe : `vigie2026`

## Qualité et Tests

Pour garantir la stabilité de l'application, une suite de tests automatisés est disponible.

### Lancer les tests

Nous recommandons d'utiliser le script dédié qui gère l'environnement et évite les problèmes de collection dans certains environnements (WSL) :

```bash
uv run python run_tests.py
```

Vous pouvez aussi utiliser `pytest` directement :
```bash
PYTHONPATH=. uv run pytest tests -v
```

Consultez le fichier [tests/README.md](tests/README.md) pour plus de détails sur l'implémentation des tests.

## Architecture

- **Interface** : [NiceGUI](https://nicegui.io/) (basé sur TailwindCSS & Quasar).
- **Backend** : Python 3.13+.
- **Base de données** : SQLite avec [SQLModel](https://sqlmodel.tiangolo.com/) (ORM basé sur SQLAlchemy & Pydantic).

## Documentation

Consultez le [USER_GUIDE.md](docs/USER_GUIDE.md) pour plus de détails sur l'utilisation du logiciel.
