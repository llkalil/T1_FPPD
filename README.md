# T1 — Filósofos Jantando (Go)

Trabalho 1 de Fundamentos de Programação Paralela e Distribuída (PUCRS). Compara quatro estratégias para o problema dos filósofos jantando e mede o efeito da sincronização no desempenho.

| Versão | Estratégia | Resultado |
|---|---|---|
| V0 | Sequencial (baseline) | referência de tempo |
| V1 | Um mutex por garfo, esquerdo → direito | deadlock |
| V2 | Mutex global + garfos | sem deadlock, sincronização excessiva |
| V3 | Garfos ordenados (menor índice primeiro) | sem deadlock, alta concorrência |

## Estrutura

```
filosofos/            código (main.go, go.mod) e run.sh (bateria de experimentos)
resultados/
  c8g.16xlarge/       dados crus (results.csv, console.txt, env.txt, deadlock_n*.txt) e parseados (summary.csv/.md)
  c8g.medium/         mesma bateria na c8g.medium (1 vCPU), para comparar com a 16xlarge
  c8g.medium-sa-east-1-teste/   log do teste de validação inicial
  parse.py            results.csv -> summary.csv/.md
  gen_report.py       gera relatorio_t1.pdf
  relatorio_t1.pdf    relatório final
```

## Rodar

Requer Go 1.21+ e bash.

```bash
cd filosofos
go build -o filosofos .
./filosofos -v 3 -n 5            # uma versão (v = 0..3), 5 filósofos
./filosofos -v 1 -n 5            # deadlock: o watchdog imprime quem segura/espera cada garfo (saída com código 3)
NS="5 48 96" RUNS=5 ./run.sh     # bateria completa -> results.csv, env.txt, deadlock_n*.txt
```

Flags: `-v` versão, `-n` filósofos, `-cycles` (20), `-think`/`-eat` (10ms), `-gap` (V1: pausa entre os dois garfos, 1ms), `-stall` (5s sem progresso = deadlock), `-csv`.

Métricas: tempo total, espera média e máxima pelos garfos, máximo de filósofos comendo ao mesmo tempo e ciclos por filósofo.

## Relatório

```bash
pip install matplotlib reportlab pymupdf
python resultados/parse.py resultados/c8g.16xlarge
python resultados/gen_report.py
```

`gen_report.py` usa fontes do Windows (Arial/Consolas); em outro SO ajuste o caminho em `F`. Antes de entregar, preencha nome/matrícula do grupo e o link do repositório no relatório.

## Ambiente dos resultados

AWS EC2 c8g.16xlarge (spot, 64 vCPUs) e c8g.medium (spot, 1 vCPU), ambas Graviton4, Amazon Linux 2023, Go 1.26.8 linux/arm64. Pensar/comer são `time.Sleep`, então o resultado não depende do número de cores.
