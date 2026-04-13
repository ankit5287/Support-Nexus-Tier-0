import multiprocessing

bind = "unix:logic_stream.sock"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 2
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Logic Stream Node Optimization
# On Oracle ARM (4 OCPUs), this will spawn ~9 workers
# for high-fidelity BERT throughput.
