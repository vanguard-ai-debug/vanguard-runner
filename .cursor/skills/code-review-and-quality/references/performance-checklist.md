# Performance Review Checklist

Use for hot paths, scalability-sensitive code, and UI. Profile when in doubt.

## Data access

- [ ] No N+1 queries; batching or joins where appropriate
- [ ] List endpoints paginated or cursor-based; no unbounded `SELECT *` on large tables
- [ ] Indexes considered for new query patterns

## Algorithms and loops

- [ ] No unbounded loops over user-controlled or external collections
- [ ] Complexity appropriate for expected input sizes

## Concurrency and I/O

- [ ] Blocking I/O not on latency-sensitive threads (async/thread pools as per stack)
- [ ] No accidental contention (locks, shared mutable state) in hot paths

## Caching and memory

- [ ] Caching strategy clear; TTL/invalidation defined if added
- [ ] Large allocations not inside tight loops; streaming for big payloads when applicable

## Frontend (if applicable)

- [ ] Avoidable re-renders addressed (memoization, stable props, list keys)
- [ ] Heavy work not on main thread without justification

## Related

Main workflow: [../SKILL.md](../SKILL.md) (Performance axis).
