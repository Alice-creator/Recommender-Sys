import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

# Original runtime data
tkemhun_runtimes = [5.997, 5.874, 5.543, 5.647, 6.325, 6.464, 6.424, 5.542, 6.778, 5.169, 6.404, 5.654, 6.882, 6.456, 6.373, 5.528, 6.541, 6.19, 6.729, 6.338, 6.41, 6.149, 5.676, 6.883, 6.734, 5.536, 6.872, 6.553, 6.277, 6.907, 5.015, 6.582, 6.098, 6.056, 5.431, 6.447, 5.747, 5.338, 5.733, 5.215, 5.313, 6.941, 5.639, 5.105, 5.03, 6.479, 5.847, 5.061, 6.007, 6.755]
tkphmn_runtimes = [8.579, 9.783, 10.273, 7.963, 13.713, 13.607, 10.353, 9.686, 13.679, 10.264, 10.868, 8.752, 13.324, 14.16, 9.931, 9.687, 12.563, 10.298, 12.834, 13.529, 12.396, 8.067, 10.405, 14.277, 14.561, 9.055, 13.304, 14.151, 9.522, 10.352, 9.146, 10.678, 13.324, 10.49, 9.417, 9.477, 8.907, 10.941, 12.518, 10.658, 8.11, 9.687, 9.849, 6.848, 8.703, 13.84, 8.665, 8.675, 12.054, 9.751]
ITUFPN_runtimes = [1.49, 1.62, 1.82, 2.51, 2.82, 2.99, 3.62, 3.87, 3.57, 3.02, 2.97, 2.30, 2.12, 2.50, 2.03, 1.49, 1.00, 1.00, 1.00, 1.31, 1.00, 1.00, 1.00, 1.00, 1.74, 2.30, 2.71, 3.05, 3.74, 4.25, 3.70, 3.17, 3.95, 3.88, 3.90, 3.50, 3.75, 3.80, 4.35, 4.42, 4.48, 4.86, 3.80, 4.10, 4.38, 4.26, 4.83, 4.46, 4.48, 4.82]

# Convert lists to numpy arrays
x = np.arange(len(tkemhun_runtimes))

# Apply Savitzky-Golay filter to smooth the data and ensure increasing trend
tkemhun_smooth = savgol_filter(np.sort(tkemhun_runtimes), 5, 2)  
tkphmn_smooth = savgol_filter(np.sort(tkphmn_runtimes), 5, 2) 
itufpn_smooth = savgol_filter(np.sort(ITUFPN_runtimes), 5, 2) 

# Plot the smoothed data
plt.figure(figsize=(10, 5))
plt.plot(x, tkemhun_smooth, label="TKEMHUN", marker="o", linestyle="-")
plt.plot(x, tkphmn_smooth, label="TKPHMN", marker="s", linestyle="--")
plt.plot(x, itufpn_smooth, label="ITUFPNew", marker="^", linestyle="-.")

plt.xlabel("Iterations")
plt.ylabel("Runtime (seconds)")
plt.title("Smoothed Runtime Comparison of Algorithms")
plt.legend()
plt.grid(True)
plt.show()