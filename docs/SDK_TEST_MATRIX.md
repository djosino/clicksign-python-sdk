# SDK Test Matrix — Required Behavioral Coverage

Every item below **must** have a corresponding test. Mark with ✓ as implemented.
Reference implementation: `../clicksign-ruby-sdk/spec/`

---

## Configuration

- [ ] Defaults: production base_url, open_timeout=2, read_timeout=10, write_timeout=10, max_retries=0, logger=None
- [ ] `environment='sandbox'` sets sandbox URL
- [ ] `environment='production'` sets production URL
- [ ] Unknown environment raises ValueError
- [ ] Accepts a logger object

## HTTP Client

- [ ] GET sends correct headers (Authorization, Content-Type, Accept)
- [ ] POST sends body as JSON
- [ ] PATCH sends body as JSON
- [ ] DELETE sends no body
- [ ] `Authorization` header has NO `Bearer` prefix — raw token only
- [ ] Raises `TimeoutError` on connect timeout
- [ ] Raises `TimeoutError` on read timeout
- [ ] Raises `TimeoutError` on connection refused

## Error handler

- [ ] 401 → `AuthenticationError`
- [ ] 403 → `AuthenticationError`
- [ ] 404 → `NotFoundError`
- [ ] 400 → `ValidationError`
- [ ] 422 → `ValidationError` with message from `errors[0].detail`
- [ ] 409 → `ConflictError`
- [ ] 429 → `RateLimitError`
- [ ] 500 → `ServerError`
- [ ] Non-JSON body → falls back to HTTP reason phrase
- [ ] JSON array body (not dict) → falls back to HTTP reason phrase, no TypeError
- [ ] `errors[0].title` used when `detail` is absent
- [ ] Empty body → falls back to HTTP reason phrase
- [ ] `status_code` exposed on exception
- [ ] `request_id` from `X-Request-Id` header
- [ ] `rate_limit_remaining` / `rate_limit_reset` on `RateLimitError`
- [ ] `retryable` is True for RateLimitError, ServerError, TimeoutError
- [ ] `retryable` is False for ValidationError, NotFoundError, AuthenticationError

## Retry

- [ ] `max_retries=0` makes exactly 1 request
- [ ] Retries on 500 (ServerError) and succeeds on next attempt
- [ ] Retries on 429 (RateLimitError) and succeeds on next attempt
- [ ] Retries on TimeoutError and succeeds on next attempt
- [ ] Does NOT retry on 422 (ValidationError)
- [ ] Raises after exhausting max_retries (1 + N total requests)
- [ ] Sleeps with exponential backoff between retries
- [ ] Sleep duration is < ceiling(attempt) (full jitter, not fixed)

## RetryBackoff

- [ ] `ceiling(1)` = 0.5
- [ ] `ceiling(2)` = 1.0
- [ ] `ceiling(10)` = 30.0 (capped)
- [ ] `delay(attempt)` returns value in [0, ceiling)
- [ ] Returns 0.0 when ceiling is 0
- [ ] Spread across multiple calls (not always the same value)

## JsonApiSerializer

- [ ] Create: no `id`, no `relationships` key when empty
- [ ] Update: includes `id`
- [ ] With relationships: included in payload
- [ ] Empty relationships: `relationships` key omitted
- [ ] nil/None attributes: passed through

## JsonApiParser

- [ ] Single object: returns as one-element list internally
- [ ] Array: returns all items
- [ ] Empty/null data: returns empty list
- [ ] Included resources parsed correctly
- [ ] Included entries without `type` filtered out
- [ ] Missing attributes/relationships default to empty dict

## QueryBuilder

- [ ] `filter(key=val)` → `filter[key]=val`
- [ ] `filter(false_val=False)` → included (False is a valid filter)
- [ ] `order('name')` → `sort=name`
- [ ] `order('-created')` → `sort=-created`
- [ ] `page(2)` → `page[number]=2`
- [ ] `per(50)` → `page[size]=50`
- [ ] `with_includes('a', 'b')` → `include=a,b`
- [ ] `fields(envelopes=['name','status'])` → `fields[envelopes]=name,status`
- [ ] All methods chainable (return builder)
- [ ] `to_params()` combines all accumulated params

## Resource base

- [ ] `resource_type` inferred from class name (snake_case + plural)
- [ ] Explicit `resource_type` overrides inference
- [ ] Inferred type handles anonymous/unnamed class safely
- [ ] `endpoint` defaults to `/resource_type`
- [ ] `endpoint` can be overridden
- [ ] `list()` returns list of instances (no args)
- [ ] `list()` raises when given args
- [ ] `retrieve(id)` returns single instance
- [ ] `create(**attrs)` returns new instance
- [ ] `update(**attrs)` sends PATCH, returns self
- [ ] `delete()` sends DELETE, returns None
- [ ] `reload()` refreshes from API
- [ ] Dynamic attribute access (`instance.name`)
- [ ] `instance['name']` via `__getitem__`
- [ ] Unknown attribute raises AttributeError (not silent)
- [ ] `id` and `relationships` accessible
- [ ] `base_path` defaults to endpoint

## QueryProxy

- [ ] `filter()` returns QueryProxy
- [ ] `order()` returns QueryProxy
- [ ] `with_includes()` returns QueryProxy
- [ ] `fields()` returns QueryProxy
- [ ] `page()` returns QueryProxy
- [ ] `per()` returns QueryProxy
- [ ] `with_includes()` raises ValueError for empty args
- [ ] `with_includes()` raises ValueError for non-string types
- [ ] `to_list()` executes request, returns list
- [ ] `first()` returns first item
- [ ] `last()` returns last item
- [ ] `count()` returns int
- [ ] Iterable (for-loop, list comprehension)

## Auto-pagination

- [ ] Yields all records across multiple pages
- [ ] Uses `links.next` when present to determine end
- [ ] When `links.next` is null, stops without extra request (even if page is exactly full)
- [ ] Falls back to item-count heuristic when API omits `links`
- [ ] Falls back: makes one extra request when last page is exactly full
- [ ] Composable with `filter` and `order`
- [ ] Default page size is 20
- [ ] Raises on API error mid-pagination

## Instrumentation

- [ ] `:request` published on successful request (method, path, status, attempt, duration_ms)
- [ ] `:request` published even when request raises error
- [ ] `:error` published with exception on HTTP error
- [ ] `:error` published on timeout (status=None)
- [ ] `:retry` published before each retry (attempt, max_retries, error, wait_ms)
- [ ] One `:request` event per attempt on retry
- [ ] Callback exception does NOT propagate to caller
- [ ] Remaining callbacks run after one raises
- [ ] With `config.logger` set: callback error logged via `logger.warning`
- [ ] Without logger: callback errors silent
- [ ] `Clicksign.on_request`, `on_retry`, `on_error` top-level helpers
- [ ] `clear()` removes all callbacks (for test teardown)
- [ ] `BulkOperationsClient` publishes `:request` and `:error`

## BulkOperationsClient

- [ ] Sends `Authorization`, `Content-Type`, `Accept` headers
- [ ] POST body is JSON
- [ ] Returns parsed body when `atomic:results` present (no exception)
- [ ] Top-level `errors` → raises exception
- [ ] 422 → `ValidationError`
- [ ] 500 → `ServerError`
- [ ] 401 → `AuthenticationError`
- [ ] Invalid JSON body → does not raise `JSONDecodeError`
- [ ] Retries on TimeoutError, succeeds on subsequent attempt
- [ ] Does NOT retry on ServerError (500) — only timeouts
- [ ] Raises after exhausting max_retries

## Services (thread-local)

- [ ] `with Services(api_key=...) as svc: svc.use(...)` routes resource calls through service client
- [ ] Does not use global client inside block
- [ ] Restores previous client after block (including on exception)
- [ ] Unknown environment raises ValueError

## Webhook

- [ ] Valid signature returns True
- [ ] Invalid signature returns False (constant-time)
- [ ] Empty payload validates correctly
- [ ] Uses `hmac.compare_digest` (not `==`)

## Resource specs (per resource)

Each resource spec must cover:
- [ ] `describe 'resource configuration'`: `resource_type` and `endpoint` values
- [ ] All CRUD methods available per route (`only:`/`except:`)
- [ ] `.filter()` with at least one filter param
- [ ] Error paths: `ValidationError` (422) for `.create`/`.update`; `NotFoundError` (404) for `.retrieve`/`.delete`
- [ ] Relationship accessors (e.g., `envelope_id`, `signer_id`)
- [ ] Routes with `except: [:update]` raise `NotImplementedError`
