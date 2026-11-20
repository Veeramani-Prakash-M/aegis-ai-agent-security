# Publish AEGIS to GitHub

The repository already exists at <https://github.com/Veeramani-Prakash-M/aegis-ai-agent-security>; changes land through pull requests. To publish this bundle to a different new repository, create a new **empty** repository on GitHub named `aegis-ai-agent-security` (do not initialize it with a README, license, or `.gitignore`).

From this project directory, run:

```bash
git init -b main
git add .
git commit -m "Build AEGIS AI agent security evaluation MVP"
git remote add origin https://github.com/Veeramani-Prakash-M/aegis-ai-agent-security.git
git push -u origin main
```

Alternatively, share the new repository URL with the project maintainer to publish the source through the connected GitHub integration.

For a resume portfolio, make the repository public only after reviewing the source and confirming it contains no private information or credentials.
