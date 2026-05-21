# Paginação e QueryProxy

## Parâmetros de página

| Constante | Valor | Uso |
|-----------|-------|-----|
| `clicksign.pagination.DEFAULT_PAGE_SIZE` | **20** | Tamanho quando `.per()` não é chamado (comportamento histórico do SDK) |
| `clicksign.pagination.MAX_PAGE_SIZE` | **50** | Máximo aceito por `.per()` no SDK (exemplos da API Clicksign usam `page[size]=50`) |
| `DOCUMENTED_API_DEFAULT_PAGE_SIZE` | **25** | Padrão documentado na API quando o cliente não envia `page[size]` |

```python
from clicksign import Envelope

# até 50 itens por página
Envelope.filter(status="draft").per(50).to_list()

# .per(100) levanta ValueError
```

## Auto-paginação

`filter(...).to_list()`, `for item in filter(...):`, `.count()` e `.last()` percorrem todas as páginas automaticamente.

### Quando parar?

1. **`links.next` presente** (prioridade): se `links.next` for `null` ou string vazia, é a última página — **não** faz outro request mesmo que a página esteja cheia.
2. **Sem `links.next`**: heurística legada — continua enquanto `len(items) >= page[size]`; se a última página vier exatamente cheia, o SDK faz **um** request extra (geralmente retorna vazio).

Implementação: `clicksign.pagination.has_next_page()`.

## `last_response` e `page_responses`

Durante a iteração, `QueryProxy.last_response` é atualizado **a cada página** (última página buscada até o momento).

```python
proxy = Envelope.filter(status="running")
seen: list[str | None] = []
for _ in proxy:
    seen.append(proxy.last_response.request_id if proxy.last_response else None)
assert len(seen) == len(proxy.page_responses)
```

`page_responses` guarda metadados de **todas** as páginas da execução atual (lista reiniciada em cada `to_list()` / novo `for`).

## Callback `on_page`

```python
def log_page(page: int, meta, items):
    print(page, meta.status if meta else None, len(items))

Envelope.filter(status="draft").on_page(log_page).to_list()
```

Útil para progresso, métricas ou integração com `instrumentation.on_request` sem duplicar lógica de paginação.

## Async

`AsyncClicksignClient` expõe o mesmo comportamento em `AsyncQueryProxy` (`async for`, `on_page`, `page_responses`).

## Referências

- Contrato: [`SDK_CONTRACT.md`](SDK_CONTRACT.md) §7
- Exemplo: [`examples/07-list-and-filter.md`](examples/07-list-and-filter.md)
