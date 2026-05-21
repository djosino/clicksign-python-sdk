Leia os recursos definidos no namespace :v3 em ~/workspace/harness/tavola/config/routes/api.rb
e compare com os arquivos em src/clicksign/resources/.

Liste:
1. Recursos do tavola que ainda não têm implementação no SDK
2. Recursos implementados que podem estar desatualizados em relação às rotas ou ao resource do tavola
3. Endpoints específicos (actions como :activate, :me, etc.) que faltam nos resources existentes

Para cada resource, observe:
- O `only:` das rotas — determina quais métodos (list/retrieve/create/update/delete) devem existir
- O arquivo em `app/resources/api/v3/` — atributos, filtros e relacionamentos disponíveis
- Actions extras no controller além do CRUD padrão

Ao final, sugira a ordem de implementação por prioridade.
