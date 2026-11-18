import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# Run this script from the project root.
df = pd.read_csv(os.path.join('data', 'unhcr_clean.csv'))
os.makedirs('figures', exist_ok=True)

# Calculate annual totals and country rankings.
host_year = df.groupby(['host_country', 'year'])['refugee_count'].sum(min_count=1).reset_index(name='refugee_total')
origin_year = df.groupby(['origin_country', 'year'])['refugee_count'].sum(min_count=1).reset_index(name='refugee_total')
host_ranking = host_year.groupby('host_country').agg(average_refugees=('refugee_total', 'mean'), years_available=('refugee_total', 'count')).sort_values('average_refugees', ascending=False)
origin_ranking = origin_year.groupby('origin_country').agg(average_refugees=('refugee_total', 'mean'), years_available=('refugee_total', 'count')).sort_values('average_refugees', ascending=False)

# Figure 1: heatmap of top host countries.
purple_cmap = LinearSegmentedColormap.from_list('custom_purples', ['#E4D7F2', '#B99AD9', '#8863B8', '#59318E', '#32145C'])
top5_hosts = host_ranking.head(5).index.tolist()
heatmap_data = (host_year[host_year['host_country'].isin(top5_hosts)].pivot(index='host_country', columns='year', values='refugee_total').reindex(top5_hosts) / 1_000_000)
fig, ax = plt.subplots(figsize=(12, 5))
heatmap = sns.heatmap(heatmap_data, cmap=purple_cmap, annot=True, fmt='.2f', linewidths=0.5, linecolor='white', cbar_kws={'label': 'Refugee Population (Millions)'}, ax=ax)
norm = heatmap.collections[0].norm
for label in heatmap.texts:
    x, y = label.get_position()
    value = heatmap_data.iloc[int(y - 0.5), int(x - 0.5)]
    rgba = purple_cmap(norm(value))
    luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
    label.set_color('white' if luminance < 0.45 else '#21152F')
    label.set_fontsize(10)
ax.set_title('Top 5 Refugee-Hosting Countries (2008–2016)', fontsize=15, fontweight='bold', pad=15)
ax.set_xlabel('Year', fontsize=11)
ax.set_ylabel('Host Country', fontsize=11)
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
plt.tight_layout()
plt.savefig(os.path.join('figures', 'figure1_heatmap.png'), dpi=300, bbox_inches='tight')
plt.close(fig)

# Figure 2: grouped bar chart of top origin countries.
top5_origins = origin_ranking.head(5).index.tolist()
bar_data = (origin_year[origin_year['origin_country'].isin(top5_origins)].pivot(index='year', columns='origin_country', values='refugee_total').reindex(index=range(2008, 2017), columns=top5_origins) / 1_000_000)
colors = ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#D55E00']
fig, ax = plt.subplots(figsize=(14, 6))
years = bar_data.index.to_numpy()
x = np.arange(len(years))
bar_width = 0.16
for i, country in enumerate(top5_origins):
    positions = x + (i - 2) * bar_width
    ax.bar(positions, bar_data[country], width=bar_width, label=country, color=colors[i], edgecolor='white', linewidth=0.4)
ax.set_title('Top 5 Refugee-Origin Countries (2008–2016)', fontsize=15, fontweight='bold', pad=18)
ax.set_xlabel('Year', fontsize=11)
ax.set_ylabel('Refugee Population (Millions)', fontsize=11)
ax.set_xticks(x)
ax.set_xticklabels(years)
ax.legend(title='Country of Origin', loc='upper left', frameon=False)
ax.grid(axis='y', linestyle='--', alpha=0.25)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.text(0.5, 0.01, 'Source: UNHCR. Countries ranked by average annual refugee population, 2008–2016.', ha='center', fontsize=9, color='dimgray')
plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(os.path.join('figures', 'figure2_bar_chart.png'), dpi=300, bbox_inches='tight')
plt.close(fig)

print('Saved figures/figure1_heatmap.png and figures/figure2_bar_chart.png')
