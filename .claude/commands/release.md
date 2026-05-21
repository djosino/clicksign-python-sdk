Prepare uma nova release do SDK:

1. Leia o CHANGELOG.md atual e os commits desde a última tag: `git log $(git describe --tags --abbrev=0)..HEAD --oneline`
2. Determine o próximo número de versão (semver) baseado nas mudanças
3. Atualize o arquivo REVISION com apenas o novo número de versão
4. Atualize o CHANGELOG.md com as mudanças agrupadas (Added, Changed, Fixed, Removed)
5. Mostre o diff e aguarde confirmação antes de commitar
