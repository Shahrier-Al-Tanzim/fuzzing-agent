# Groq — per-run metrics

Runs: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12

## Run-level summary

| Run | Model | Status | Attempts | Total tokens |
|---|---|---|---|---|
| 1 | llama-3.3-70b-versatile | PASSED (5 iters) | 7 | 52,924 |
| 2 | llama-3.3-70b-versatile | unknown | 9 | 69,941 |
| 3 | llama-3.3-70b-versatile | PASSED (5 iters) | 7 | 55,996 |
| 4 | llama-3.3-70b-versatile | STOPPED/FAILED (3 iters) | 6 | 49,693 |
| 5 | llama-3.3-70b-versatile | PASSED (2 iters) | 3 | 30,099 |
| 6 | llama-3.3-70b-versatile | PASSED (5 iters) | 9 | 72,100 |
| 7 | llama-3.3-70b-versatile | PASSED (5 iters) | 12 | 102,484 |
| 8 | llama-3.3-70b-versatile | PASSED (5 iters) | 11 | 95,470 |
| 9 | llama-3.3-70b-versatile | PASSED (5 iters) | 7 | 69,247 |
| 10 | llama-3.3-70b-versatile | PASSED (0 iters) | 5 | 53,230 |
| 11 | llama-3.3-70b-versatile | STOPPED/FAILED (0 iters) | 4 | 36,245 |
| 12 | llama-3.3-70b-versatile | PASSED (1 iters) | 11 | 108,288 |

## Run 1

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 34% | 55% | 33% | 4 | 0 | 500 | 63.6 |
| 1 | 37% | 63% | 25% | 4 | 0 | 500 | 35.8 |
| 2 | 33% | 74% | 23% | 5 | 0 | 500 | 41.9 |
| 3 | 39% | 84% | 28% | 5 | 0 | 500 | 40.3 |
| 4 | 39% | 84% | 23% | 5 | 0 | 500 | 44.8 |

## Run 2

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 39% | 53% | 34% | 2 | 0 | 500 | 21.8 |
| 1 | 31% | 58% | 19% | 2 | 0 | 500 | 80.3 |
| 2 | 27% | 63% | 18% | 2 | 0 | 500 | 78.2 |
| 3 | 38% | 71% | 20% | 3 | 0 | 500 | 85.5 |

## Run 3

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 36% | 63% | 35% | 4 | 0 | 500 | 33.0 |
| 1 | 30% | 74% | 22% | 4 | 0 | 500 | 37.8 |
| 2 | 26% | 84% | 15% | 4 | 0 | 500 | 52.0 |
| 3 | 22% | 84% | 25% | 4 | 0 | 500 | 60.4 |
| 4 | 20% | 87% | 21% | 4 | 0 | 500 | 85.8 |

## Run 4

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 39% | 55% | 35% | 3 | 0 | 500 | 22.2 |
| 1 | 40% | 68% | 22% | 3 | 0 | 500 | 45.1 |
| 2 | 35% | 84% | 21% | 3 | 0 | 500 | 44.4 |

## Run 5

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 3 | 40% | 87% | 20% | 3 | 0 | 500 | 65.5 |
| 4 | 42% | 90% | 19% | 3 | 0 | 500 | 64.8 |

## Run 6

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 47% | 47% | 28% | 3 | 0 | 500 | 60.5 |
| 1 | 47% | 50% | 20% | 3 | 0 | 500 | 76.2 |
| 2 | 42% | 53% | 12% | 3 | 0 | 500 | 81.6 |
| 3 | 42% | 55% | 13% | 4 | 0 | 500 | 62.5 |
| 4 | 7% | 55% | 5% | 4 | 0 | 500 | 45.3 |

## Run 7

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 12% | 53% | 40% | 2 | 0 | 500 | 158.7 |
| 1 | 15% | 55% | 33% | 2 | 0 | 500 | 48.7 |
| 2 | 12% | 55% | 33% | 2 | 0 | 500 | 91.4 |
| 3 | 13% | 55% | 23% | 4 | 0 | 500 | 135.7 |
| 4 | 23% | 58% | 38% | 4 | 0 | 500 | 1760.7 |

## Run 8

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 50% | 34% | 19% | 1 | 0 | 500 | 147.4 |
| 1 | 49% | 34% | 8% | 1 | 0 | 500 | 132.8 |
| 2 | 52% | 45% | 5% | 3 | 0 | 500 | 50.2 |
| 3 | 53% | 53% | 20% | 3 | 0 | 500 | 49.4 |
| 4 | 40% | 60% | 17% | 3 | 0 | 500 | 52.0 |

## Run 9

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 32% | 55% | 37% | 4999 | 0 | 500 | 40.1 |
| 1 | 37% | 68% | 31% | 4999 | 0 | 500 | 102.7 |
| 2 | 46% | 76% | 21% | 5000 | 0 | 500 | 48.6 |
| 3 | 40% | 84% | 22% | 5000 | 0 | 500 | 55.3 |
| 4 | 42% | 84% | 20% | 5000 | 0 | 500 | 53.8 |

## Run 10

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 55% | 60% | 32% | 40138 | 51 | 500 | 44.7 |
| 1 | 53% | 66% | 26% | 51462 | 66 | 500 | 49.2 |
| 2 | 54% | 79% | 21% | 52029 | 74 | 500 | 50.9 |
| 3 | 55% | 79% | 21% | 52029 | 78 | 500 | 63.3 |
| 4 | 75% | 82% | 10% | 52029 | 49 | 500 | 38.5 |

## Run 12

| Iter | Accept | Coverage | Novelty | Max depth | Findings | Examples | Elapsed (s) |
|---|---|---|---|---|---|---|---|
| 0 | 59% | 55% | 23% | 49599 | 22 | 500 | 234.0 |
| 1 | 54% | 63% | 21% | 49599 | 27 | 500 | 126.3 |
| 2 | 53% | 71% | 22% | 49599 | 32 | 500 | 142.5 |
| 3 | 18% | 74% | 25% | 49599 | 40 | 500 | 103.0 |
| 4 | 52% | 74% | 23% | 49599 | 58 | 500 | 83.9 |
