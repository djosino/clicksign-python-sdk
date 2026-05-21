Prepare uma nova release do SDK:

1. Leia o CHANGELOG.md atual e os commits desde a última release: `git log $(git describe --tags --abbrev=0 2>/dev/null || echo main)..HEAD --oneline`
2. Determine o próximo número de versão (semver) baseado nas mudanças
3. Atualize o arquivo REVISION com apenas o novo número de versão
4. Atualize o CHANGELOG.md com as mudanças agrupadas (Added, Changed, Fixed, Removed)
5. Mostre o diff e aguarde confirmação antes de commitar
6. Após confirmação, oriente a branch de release `release/<version>` — ver `docs/RELEASE.md`
   - Commit REVISION + CHANGELOG no `main`, push
   - `git checkout -b release/X.Y.Z` e `git push -u origin release/X.Y.Z`
   - `git push origin release/X.Y.Z` dispara CI: TestPyPI → PyPI (secrets `TEST_PYPI_API_TOKEN` + `PYPI_API_TOKEN`)
   - Branch `release/X.Y.Z` deve coincidir com `REVISION` — ver `docs/RELEASE.md`
   - Após CI verde: merge `release/X.Y.Z` no `main`
