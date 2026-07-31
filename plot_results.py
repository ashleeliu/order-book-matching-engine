#Plot spread and mid-price behavior simulation run

import json
import matplotlib.pyplot as plt

with open("simulation_output.json") as f:
    data = json.load(f)

spreads = data["spread_history"]
mids = data["mid_price_history"]

fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

axes[0].plot(mids, linewidth=0.8, color="#2563eb")
axes[0].set_title("Simulated Mid-Price Path")
axes[0].set_ylabel("Mid Price")

axes[1].plot(spreads, linewidth=0.8, color="#dc2626")
axes[1].set_title("Bid-Ask Spread Over Time")
axes[1].set_ylabel("Spread")
axes[1].set_xlabel("Order Sequence")

plt.tight_layout()
plt.savefig("simulation_results.png", dpi=150)
print("Saved simulation_results.png")
