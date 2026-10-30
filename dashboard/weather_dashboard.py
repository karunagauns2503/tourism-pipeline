import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DB_PATH = r"data\gold\goa_tourism.duckdb"

con = duckdb.connect(DB_PATH, read_only=True)

monthly = con.sql("""
    SELECT *
    FROM v_monthly_weather
    ORDER BY year, month
""").df()

season = con.sql("""
    SELECT *
    FROM v_season_weather
    ORDER BY
        CASE season
            WHEN 'Winter' THEN 1
            WHEN 'Summer' THEN 2
            WHEN 'Monsoon' THEN 3
            WHEN 'Post-monsoon' THEN 4
        END
""").df()

con.close()

sns.set_theme(style="whitegrid")

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# 1. Monthly Rainfall
sns.lineplot(
    data=monthly,
    x="month_name",
    y="total_rain_mm",
    marker="o",
    ax=axes[0, 0]
)

axes[0, 0].set_title("Monthly Rainfall")
axes[0, 0].set_xlabel("Month")
axes[0, 0].set_ylabel("Total Rainfall (mm)")
axes[0, 0].tick_params(axis="x", rotation=45)

# 2. Monthly Temperature
sns.lineplot(
    data=monthly,
    x="month_name",
    y="avg_max_temp_c",
    marker="o",
    ax=axes[0, 1]
)

axes[0, 1].set_title("Monthly Average Maximum Temperature")
axes[0, 1].set_xlabel("Month")
axes[0, 1].set_ylabel("Temperature (°C)")
axes[0, 1].tick_params(axis="x", rotation=45)

# 3. Rainy Days
sns.barplot(
    data=monthly,
    x="month_name",
    y="rainy_days",
    ax=axes[1, 0]
)

axes[1, 0].set_title("Rainy Days by Month")
axes[1, 0].set_xlabel("Month")
axes[1, 0].set_ylabel("Number of Rainy Days")
axes[1, 0].tick_params(axis="x", rotation=45)

# 4. Season Comparison
season_melted = season.melt(
    id_vars="season",
    value_vars=["avg_daily_rain_mm", "heavy_rain_days"],
    var_name="Metric",
    value_name="Value"
)

sns.barplot(
    data=season_melted,
    x="season",
    y="Value",
    hue="Metric",
    ax=axes[1, 1]
)

axes[1, 1].set_title("Season-wise Weather Comparison")
axes[1, 1].set_xlabel("Season")
axes[1, 1].set_ylabel("Value")
axes[1, 1].tick_params(axis="x", rotation=20)

plt.suptitle(
    "Goa Tourism Analytics - Weather Analysis",
    fontsize=18,
    fontweight="bold"
)

plt.tight_layout()

output_path = "dashboard\weather_dashboard.png"

plt.savefig(output_path, dpi=300, bbox_inches="tight")

plt.close()

print("Weather dashboard created successfully!")
print(f"Saved as: {output_path}")