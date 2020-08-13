from warehouse import Warehouse
from warehouse_parallel import train_parallel
import matplotlib.pyplot as plt

env = Warehouse(8, 5, 5)
env.render()
n_proc = 4
n_episodes = 6000
update_interval = 500

cache_sizes = range(10, 110, 10)
exec_times = [train_parallel(env, n_proc=n_proc, update_interval=update_interval, n_episodes=n_episodes,
                             cache_size=cache_size, n_steps=100, l_rate=0.5, d_rate=0.99, max_e_rate=1,
                             min_e_rate=0.001, e_d_rate=0.1)[-1] for cache_size in cache_sizes]

plt.plot(cache_sizes, exec_times)
plt.xlabel("Cache size")
plt.ylabel("Execution time in s")
plt.show()