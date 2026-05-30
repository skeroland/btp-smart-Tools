# Deploiement BTP Smart Tools - Cartouches uniquement

Le site est maintenant concentre uniquement sur les cartouches :

- generation de cartouches PDF ;
- modeles de cartouche ;
- batch PDF ;
- compte, credits et paiement ;
- aide pour les cartouches.

Les modules non finalises ne sont plus visibles sur le site public.

## Fichiers importants a envoyer

- `app.py`
- `requirements.txt`
- `Procfile`
- `render.yaml`
- `.python-version`
- `.env.example`
- `.gitignore`

Ne pas envoyer le dossier `data/` ni `__pycache__/`.

## Commandes Git a utiliser

Depuis le dossier du projet :

```powershell
git init
git add app.py requirements.txt Procfile render.yaml .python-version .env.example .gitignore DEPLOIEMENT_GIT_CARTOUCHES.md
git commit -m "Version cartouches uniquement"
```

Ensuite, si le depot GitHub existe deja :

```powershell
git remote add origin VOTRE_LIEN_GITHUB
git branch -M main
git push -u origin main
```

Si le depot GitHub est deja connecte :

```powershell
git add app.py .gitignore DEPLOIEMENT_GIT_CARTOUCHES.md
git commit -m "Nettoyage site cartouches uniquement"
git push
```

## Sur Render

Apres le `git push`, Render redeploie automatiquement si le site est connecte au depot GitHub.

Verifier ensuite :

- page accueil ;
- connexion / creation de compte ;
- generateur cartouche ;
- modeles cartouche ;
- batch PDF ;
- paiement test.
