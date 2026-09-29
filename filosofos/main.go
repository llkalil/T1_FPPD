// Filósofos jantando: V0 sequencial, V1 deadlock, V2 mutex global, V3 ordenação de garfos.
// Uso: go run . -v 3 -n 5 -cycles 20 -think 10ms -eat 10ms [-csv]
package main

import (
	"flag"
	"fmt"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

const (
	stThinking int32 = iota
	stWaitLeft
	stHoldLeftWaitRight
	stEating
)

type phil struct {
	waitSum, waitMax time.Duration
	cycles           int
	_                [40]byte // evita false sharing entre filósofos
}

func main() {
	ver := flag.Int("v", 3, "versão: 0 sequencial, 1 deadlock, 2 mutex global, 3 garfos ordenados")
	n := flag.Int("n", 5, "número de filósofos")
	cycles := flag.Int("cycles", 20, "ciclos por filósofo")
	think := flag.Duration("think", 10*time.Millisecond, "tempo pensando")
	eat := flag.Duration("eat", 10*time.Millisecond, "tempo comendo")
	gap := flag.Duration("gap", time.Millisecond, "V1: pausa entre pegar o 1º e o 2º garfo (torna o deadlock provável)")
	stall := flag.Duration("stall", 5*time.Second, "sem progresso por este tempo = deadlock")
	csv := flag.Bool("csv", false, "imprime só uma linha CSV")
	flag.Parse()
	if *n < 2 || *ver < 0 || *ver > 3 {
		fmt.Fprintln(os.Stderr, "n>=2 e v em 0..3")
		os.Exit(1)
	}

	forks := make([]sync.Mutex, *n)
	var global sync.Mutex
	state := make([]int32, *n)
	var progress, eating, maxEating atomic.Int64
	ps := make([]phil, *n)

	acquire := func(id int) {
		l, r := id, (id+1)%*n
		switch *ver {
		case 1:
			atomic.StoreInt32(&state[id], stWaitLeft)
			forks[l].Lock()
			atomic.StoreInt32(&state[id], stHoldLeftWaitRight)
			time.Sleep(*gap)
			forks[r].Lock()
		case 2:
			global.Lock() // segurado até o fim de comer: só 1 filósofo por vez
			forks[l].Lock()
			forks[r].Lock()
		case 3:
			if l > r { // sempre o garfo de menor índice primeiro: sem espera circular
				l, r = r, l
			}
			forks[l].Lock()
			forks[r].Lock()
		}
	}
	release := func(id int) {
		l, r := id, (id+1)%*n
		if *ver == 0 {
			return
		}
		forks[l].Unlock()
		forks[r].Unlock()
		if *ver == 2 {
			global.Unlock()
		}
	}

	worker := func(id int) {
		p := &ps[id]
		for c := 0; c < *cycles; c++ {
			atomic.StoreInt32(&state[id], stThinking)
			time.Sleep(*think)
			t0 := time.Now()
			if *ver != 0 {
				acquire(id)
			}
			w := time.Since(t0)
			atomic.StoreInt32(&state[id], stEating)
			cur := eating.Add(1)
			for {
				m := maxEating.Load()
				if cur <= m || maxEating.CompareAndSwap(m, cur) {
					break
				}
			}
			time.Sleep(*eat)
			eating.Add(-1)
			release(id)
			p.waitSum += w
			if w > p.waitMax {
				p.waitMax = w
			}
			p.cycles++
			progress.Add(1)
		}
	}

	done := make(chan struct{})
	start := time.Now()
	go func() {
		if *ver == 0 {
			for i := 0; i < *n; i++ {
				worker(i)
			}
		} else {
			var wg sync.WaitGroup
			for i := 0; i < *n; i++ {
				wg.Add(1)
				go func(i int) { defer wg.Done(); worker(i) }(i)
			}
			wg.Wait()
		}
		close(done)
	}()

	// watchdog: sem progresso por 'stall' => deadlock, imprime evidência
	last, lastAt := int64(-1), time.Now()
	tick := time.NewTicker(100 * time.Millisecond)
	for running := true; running; {
		select {
		case <-done:
			running = false
		case <-tick.C:
			if p := progress.Load(); p != last {
				last, lastAt = p, time.Now()
			} else if time.Since(lastAt) > *stall {
				report(*csv, *ver, *n, "DEADLOCK", time.Since(start), ps, maxEating.Load())
				if !*csv {
					fmt.Println("\n== Evidência de deadlock ==")
					for i := 0; i < *n; i++ {
						s := atomic.LoadInt32(&state[i])
						fmt.Printf("filósofo %d: %s | ciclos=%d\n", i, describe(i, *n, s), ps[i].cycles)
					}
				}
				os.Exit(3)
			}
		}
	}
	report(*csv, *ver, *n, "OK", time.Since(start), ps, maxEating.Load())
}

func describe(i, n int, s int32) string {
	l, r := i, (i+1)%n
	switch s {
	case stHoldLeftWaitRight:
		return fmt.Sprintf("tem garfo %d, ESPERA garfo %d (em posse do filósofo %d)", l, r, r)
	case stWaitLeft:
		return fmt.Sprintf("esperando garfo %d", l)
	case stEating:
		return "comendo"
	}
	return "pensando"
}

func report(csv bool, ver, n int, status string, total time.Duration, ps []phil, maxEat int64) {
	var sum, mx time.Duration
	var cnt int
	cs := make([]string, len(ps))
	for i, p := range ps {
		sum += p.waitSum
		cnt += p.cycles
		if p.waitMax > mx {
			mx = p.waitMax
		}
		cs[i] = fmt.Sprint(p.cycles)
	}
	avg := time.Duration(0)
	if cnt > 0 {
		avg = sum / time.Duration(cnt)
	}
	ms := func(d time.Duration) float64 { return float64(d.Microseconds()) / 1000 }
	if csv {
		// versao,n,status,total_ms,espera_media_ms,espera_max_ms,max_comendo,ciclos_por_filosofo
		fmt.Printf("V%d,%d,%s,%.2f,%.3f,%.3f,%d,%s\n", ver, n, status, ms(total), ms(avg), ms(mx), maxEat, strings.Join(cs, ";"))
		return
	}
	fmt.Printf("V%d n=%d status=%s\n  tempo total:        %.2f ms\n  espera média:       %.3f ms\n  maior espera:       %.3f ms\n  máx. comendo ao mesmo tempo: %d\n  ciclos por filósofo: %s\n",
		ver, n, status, ms(total), ms(avg), ms(mx), maxEat, strings.Join(cs, " "))
}
