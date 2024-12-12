import numpy as np
from scipy.stats import kendalltau, pearsonr, spearmanr

pred = [10, 20, 30, 40, 50]
gt = [12, 22, 28, 40, 50]


def calculate_psk(pred, gt):
    pearson_corr, pearson_p_value = pearsonr(pred, gt)
    print(f"Pearson correlation (r): {pearson_corr:.4f}, p-value: {pearson_p_value:.4f}")

    spearman_corr, spearman_p_value = spearmanr(pred, gt)
    print(f"Spearman correlation (ρ): {spearman_corr:.4f}, p-value: {spearman_p_value:.4f}")

    kendall_corr, kendall_p_value = kendalltau(pred, gt)
    print(f"Kendall-Tau correlation (τ): {kendall_corr:.4f}, p-value: {kendall_p_value:.4f}")
