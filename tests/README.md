# Documentation des Tests - Vigie

Cette suite de tests utilise **pytest** pour valider la logique métier, l'intégrité de la base de données et les comportements spécifiques des catégories.

## Architecture des Tests

### Isolation de la Base de Données
Les tests utilisent une base de données SQLite **en mémoire** (`sqlite://`) pour chaque session de test. Cela garantit que :
1. Les tests sont rapides.
2. Les données de production ne sont jamais impactées.
3. Chaque test repart d'un état vierge.

### Stratégie de "Lazy Loading" (Chargement Différé)
En raison de l'utilisation de **NiceGUI**, l'importation de certains modules UI peut déclencher l'initialisation de services (comme le stockage utilisateur) qui nécessitent une boucle d'événements active.

Pour permettre à `pytest` de collecter les tests sans erreur :
- Les imports de l'application dans `tests/conftest.py` sont effectués **à l'intérieur** des fixtures.
- Les appels à la fonction `frame()` dans `app/ui/*.py` ont été déplacés à l'intérieur des fonctions de page pour éviter toute exécution au moment de l'import.

## Fixtures Disponibles

- `session` : Fournit une session de base de données SQLModel propre.
- `default_categories` : Initialise les catégories par défaut (LOYER, REVERSEMENT, etc.) via le service de bootstrap.
- `test_account` : Crée un compte bancaire de test.
- `test_lot` : Crée un lot de test.

## Contenu des Tests

- `test_categories.py` : Vérifie la création des catégories, les types par défaut et la propriété "Reversement direct".
- `test_operations.py` : Valide la création d'opérations et le comportement spécifique des catégories marquées comme "is_reversement" (celles qui permettent de se passer d'un Lot).

## Exécution

Utilisez le script racine :
```bash
uv run python run_tests.py
```
Ce script configure automatiquement le `PYTHONPATH` et lance la suite complète.
