import matplotlib.pyplot as plt
import json

for g in range(1, 11):
    val = json.load(open(f"hist/genes{g}.json", encoding="UTF-8"))["history"]
    steps = [i for i in range(len(val))]

    count = 10_000

    m = len(val) // count
    for i in range(m):
        x = steps[i * count:(i + 1) * count]
        y = val[i * count:(i + 1) * count]

        print(f'{g}/11 {i + 1}/{m}')

        f = plt.bar(x, y)

        plt.savefig(f'ims/s{g}-g{i}.png')

        plt.clf()
