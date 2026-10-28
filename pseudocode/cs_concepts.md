# Computer science ideas I used

Three short pieces that show ideas from computer science in my program. They are simplified.

## 1. Cooperative scheduling

The board has no threads. So one loop does everything, and background jobs run between control steps.

```python
jobs = {}                                   # name -> (period, next_time, function)

def register(name, period_ms, function):
    jobs[name] = (period_ms, now() + period_ms, function)

def run_due_jobs():
    for name, (period, next_time, function) in jobs.items():
        if now() >= next_time:
            function()
            jobs[name] = (period, max(next_time + period, now()), function)
```

If a job runs late, its next time moves forward from now, so it never runs several times in a row to catch up.

## 2. A wall map with shared edges

Every wall belongs to two cells. Storing it twice risks the two copies disagreeing, so every write updates both.

```python
def set_edge(x, y, direction, value):
    edges[y][x][direction] = value
    nx, ny = neighbour(x, y, direction)
    if inside(nx, ny):
        edges[ny][nx][opposite(direction)] = value
```

## 3. Dijkstra with a bucket queue

When every step costs a small whole number, a ring of lists can replace a heap. Adding and taking a node are then O(1).

```python
def cheapest_route(start, goals, step_cost, max_step):
    ring = max_step + 1
    cost = {start: 0}
    parent = {}
    buckets = [[] for _ in range(ring)]
    buckets[0].append(start)
    c = 0
    while any(buckets):
        for node in take_all(buckets[c % ring]):
            if cost[node] != c:
                continue                     # a cheaper copy was already handled
            if node in goals:
                return walk_back(parent, node)
            for nxt in neighbours(node):
                new = c + step_cost(node, nxt)
                if new < cost.get(nxt, INF):
                    cost[nxt] = new
                    parent[nxt] = node
                    buckets[new % ring].append(nxt)
        c += 1
    return None
```

This is the textbook idea. My real planner uses it on a graph where each node is a cell plus a heading, so turns can cost time. The main README explains why under [Maze solving algorithm](../README.md#maze-solving-algorithm).
