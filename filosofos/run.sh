#!/usr/bin/env bash
# Roda todas as versões RUNS vezes para cada N em NS. Saída: results.csv + env.txt
# Ex.: NS="5 48 96" RUNS=5 ./run.sh
set -u
cd "$(dirname "$0")"
NS=${NS:-"5 48 96"}
RUNS=${RUNS:-5}
V1_RUNS=${V1_RUNS:-10}   # V1 tenta mais vezes: precisa capturar deadlock
OUT=results.csv

go build -o filosofos . || exit 1

{
  echo "data: $(date -u +%FT%TZ)"
  go version
  uname -srm
  lscpu | grep -E 'Model name|^CPU\(s\)|Thread|Core|Socket'
  echo "GOMAXPROCS padrão = nproc = $(nproc)"
  echo "compilar: go build -o filosofos ."
  echo "executar: NS=\"$NS\" RUNS=$RUNS ./run.sh"
} > env.txt

echo "versao,n,status,total_ms,espera_media_ms,espera_max_ms,max_comendo,ciclos_por_filosofo" > $OUT
for n in $NS; do
  for v in 0 1 2 3; do
    r=$RUNS; [ $v = 1 ] && r=$V1_RUNS
    for i in $(seq $r); do
      ./filosofos -v $v -n $n -csv | tee -a $OUT
    done
  done
  # evidência legível de deadlock (última execução V1 que travar)
  for i in $(seq 20); do
    ./filosofos -v 1 -n $n > deadlock_n$n.txt && continue
    break
  done
done

echo; echo "== médias (execuções OK) =="
awk -F, 'NR>1 && $3=="OK"{k=$1" n="$2; c[k]++; t[k]+=$4; w[k]+=$5; if($6>m[k])m[k]=$6; if($7>e[k])e[k]=$7}
  NR>1 && $3=="DEADLOCK"{d[$1" n="$2]++}
  END{printf "%-10s %4s %10s %10s %10s %8s %5s\n","versao","runs","total_ms","espera_ms","espmax_ms","comendo","dead";
      for(k in c) printf "%-10s %4d %10.1f %10.3f %10.3f %8d %5d\n",k,c[k],t[k]/c[k],w[k]/c[k],m[k],e[k],d[k]+0;
      for(k in d) if(!(k in c)) printf "%-10s %4d %10s %10s %10s %8s %5d\n",k,0,"-","-","-","-",d[k]}' $OUT | { read -r h; echo "$h"; sort; }
