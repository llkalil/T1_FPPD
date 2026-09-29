#!/usr/bin/env bash
# Varre GOMAXPROCS (nº de cores usados pelo runtime do Go) na mesma máquina. Saída: gmp.csv + env_gmp.txt
# Ex.: GMPS="1 2 4 8 16 64" ./run_gmp.sh
set -u
cd "$(dirname "$0")"
GMPS=${GMPS:-"1 2 4 8 16 64"}
go build -o filosofos . || exit 1
{ date -u +%FT%TZ; go version; lscpu | grep -E 'Model name|^CPU\(s\)'; echo "GMPS=$GMPS"; } > env_gmp.txt 2>&1
echo "gomaxprocs,versao,n,status,total_ms,espera_media_ms,espera_max_ms,max_comendo,ciclos_por_filosofo" > gmp.csv
for g in $GMPS; do
  for i in 1 2 3 4 5; do
    for n in 48 96; do GOMAXPROCS=$g ./filosofos -v 3 -n $n -csv | sed "s/^/$g,/" | tee -a gmp.csv; done
  done
  for i in 1 2 3; do GOMAXPROCS=$g ./filosofos -v 2 -n 48 -csv | sed "s/^/$g,/" | tee -a gmp.csv; done
done
