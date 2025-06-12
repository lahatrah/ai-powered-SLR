#### imports #####

import pandas as pd
import pycountry_convert as pc
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import cartopy.feature as cfeature


def normalize_dataset(dataset):

    dataset.drop_duplicates(inplace=True)
    dataset.reset_index(drop=True,inplace=True)

    dataset["source_type"] = dataset["source_type"].astype(int)
    dataset["year"] = dataset["year"].astype(int)
    dataset["country"] = dataset["country"].astype(str)
    dataset["y"] = dataset["y"].astype(float)
    dataset["x"] = dataset["x"].astype(float)

    def country_to_continent(country_name):
        try:
            country_code = pc.country_name_to_country_alpha2(country_name)
            continent_code = pc.country_alpha2_to_continent_code(country_code)
            return {
                'AF': 'Africa',
                'AS': 'Asia',
                'EU': 'Europe',
                'NA': 'North America',
                'SA': 'South America',
                'OC': 'Oceania',
                'AN': 'Antarctica'
            }[continent_code]
        except:
            return 'Unknown'
    
    dataset['region'] = dataset['country'].apply(country_to_continent)


def world_map(dataset,title="",species="",save_to_file=None):
    plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_facecolor('white')  
    ax.add_feature(cfeature.LAND, facecolor='#D3D3D3', edgecolor='none')  
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='black')  
    ax.coastlines(color='black', linewidth=0.5)  
    ax.set_global()
    ax.scatter(dataset["x"], dataset["y"], transform=ccrs.PlateCarree(), color='red', s=10, alpha=0.6)
    plt.title(title)
    ax.text(0.02, -0.05,species, transform=ax.transAxes, fontsize=10)
    plt.savefig(save_to_file, bbox_inches='tight', dpi=300)
    plt.show()

def plot_evolution_yearly(dataset,save_to_file=None):
    grouped = dataset.groupby(['year', 'region', 'country']).size().reset_index(name='occurrences')

    fig, axs = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    axs = axs.ravel()

    for idx, region in enumerate(grouped['region'].unique()[:4]):
        region_data = grouped[grouped['region'] == region]
        countries = region_data['country'].unique()
        country_map = {c: i for i, c in enumerate(countries)}
        for _, row in region_data.iterrows():
            y = country_map[row['country']] + np.random.uniform(-0.3, 0.3)
            size = row['occurrences'] * 20
            color = 'purple' if size < 40 else 'blue' if size < 200 else 'darkblue'
            axs[idx].scatter(row['year'], y, s=size, alpha=0.6, c=color)
        axs[idx].set_yticks(range(len(countries)))
        axs[idx].set_yticklabels(countries)
        axs[idx].set_title(region)
        axs[idx].set_xlabel("Collection Year")
        axs[idx].set_xlim(1960, 2014)

    # Add legend
    legend_elements = [
        plt.scatter([], [], s=20, c='purple', alpha=0.6, label='1–2'),
        plt.scatter([], [], s=100, c='blue', alpha=0.6, label='2–10'),
        plt.scatter([], [], s=500, c='darkblue', alpha=0.6, label='10–50')
    ]
    fig.legend(handles=legend_elements, loc='center', bbox_to_anchor=(0.55, 0.55),markerscale=0.7)

    plt.tight_layout()
    plt.savefig(save_to_file, dpi=300, bbox_inches='tight')
    plt.show()