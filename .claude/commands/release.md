Prepare uma nova release do SDK:

1. Leia o CHANGELOG.md atual e os commits desde a última release: `git log $(git describe --tags --abbrev=0 2>/dev/null || echo main)..HEAD --oneline`
2. Determine o próximo número de versão (semver) baseado nas mudanças
3. Atualize o arquivo REVISION com apenas o novo número de versão
4. Atualize o CHANGELOG.md com as mudanças agrupadas (Added, Changed, Fixed, Removed)
5. Mostre o diff e aguarde confirmação antes de commitar
6. Após confirmação, oriente a branch de release: `release/<version>` (ex.: `release/0.1.2`)
   - `git checkout -b release/0.1.2` (a partir de `main` com REVISION/CHANGELOG já atualizados)
   - `git push -u origin release/0.1.2` → dispara `.github/workflows/publish-testpypi.yml` (TestPyPI)
   - A branch deve coincidir com `REVISION` (`release/0.1.2` + `REVISION=0.1.2`)
