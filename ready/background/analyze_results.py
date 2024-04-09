import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def load_results(filename):
    """Load optimization results from a CSV file."""
    return pd.read_csv(filename)

def plot_pairplot(df):
    """Plot pair plots of parameters vs. performance metrics."""
    sns.pairplot(df)
    plt.show()

def plot_heatmap(df, x_param, y_param, metric):
    """Plot a heatmap for two parameters affecting a performance metric."""
    pivot_table = df.pivot_table(values=metric, index=x_param, columns=y_param, aggfunc='mean')
    sns.heatmap(pivot_table, cmap="viridis")
    plt.show()

if __name__ == "__main__":
    results_df = load_results('optimization_results.csv')
    
    # Example usage
    plot_pairplot(results_df[['rsi_entry', 'atr_multiplier', 'total_pnl', 'win_rate', 'max_drawdown']])
    plot_heatmap(results_df, 'rsi_entry', 'atr_multiplier', 'total_pnl')
