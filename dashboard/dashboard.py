import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DB_PATH = r"C:\tourism-pipeline\tourism-pipeline-janhavi-gold\data\gold\goa_tourism.duckdb"

con = duckdb.connect(DB_PATH, read_only=True)

places = con.sql("""
    SELECT *
    FROM dim_place
""").df()

monthly = con.sql("""
    SELECT *
    FROM v_monthly_weather
    ORDER BY year, month
""").df()

con.close()

# -----------------------------
# Basic calculations
# -----------------------------

total_places = len(places)
average_rating = places["rating"].mean()
total_rainfall = monthly["total_rain_mm"].sum()
average_temperature = monthly["avg_max_temp_c"].mean()

outdoor_places = places["is_outdoor"].sum()
indoor_places = len(places) - outdoor_places

# -----------------------------
# Dashboard
# -----------------------------

sns.set_theme(style="whitegrid")

fig = plt.figure(figsize=(16, 9))

fig.suptitle(
    "GOA TOURISM ANALYTICS",
    fontsize=24,
    fontweight="bold",
    y=0.96
)

fig.text(
    0.5,
    0.925,
    "Overview of Tourist Places and Weather Conditions",
    ha="center",
    fontsize=13
)

# -----------------------------
# KPI 1
# -----------------------------

ax1 = fig.add_axes([0.06, 0.73, 0.20, 0.13])
ax1.axis("off")

ax1.text(
    0.5, 0.62,
    f"{total_places}",
    ha="center",
    fontsize=30,
    fontweight="bold"
)

ax1.text(
    0.5, 0.18,
    "Tourist Places",
    ha="center",
    fontsize=12
)

# -----------------------------
# KPI 2
# -----------------------------

ax2 = fig.add_axes([0.29, 0.73, 0.20, 0.13])
ax2.axis("off")

ax2.text(
    0.5, 0.62,
    f"{average_rating:.2f}",
    ha="center",
    fontsize=30,
    fontweight="bold"
)

ax2.text(
    0.5, 0.18,
    "Average Rating",
    ha="center",
    fontsize=12
)

# -----------------------------
# KPI 3
# -----------------------------

ax3 = fig.add_axes([0.52, 0.73, 0.20, 0.13])
ax3.axis("off")

ax3.text(
    0.5, 0.62,
    f"{average_temperature:.1f}°C",
    ha="center",
    fontsize=30,
    fontweight="bold"
)

ax3.text(
    0.5, 0.18,
    "Average Temperature",
    ha="center",
    fontsize=12
)

# -----------------------------
# KPI 4
# -----------------------------

ax4 = fig.add_axes([0.75, 0.73, 0.20, 0.13])
ax4.axis("off")

ax4.text(
    0.5, 0.62,
    f"{total_rainfall:.0f} mm",
    ha="center",
    fontsize=30,
    fontweight="bold"
)

ax4.text(
    0.5, 0.18,
    "Total Rainfall",
    ha="center",
    fontsize=12
)

# -----------------------------
# Chart 1
# -----------------------------

ax5 = fig.add_axes([0.07, 0.12, 0.40, 0.48])

place_counts = pd.DataFrame({
    "Category": ["Outdoor", "Indoor"],
    "Number of Places": [outdoor_places, indoor_places]
})

sns.barplot(
    data=place_counts,
    x="Category",
    y="Number of Places",
    ax=ax5
)

ax5.set_title(
    "Tourist Places by Category",
    fontsize=16,
    fontweight="bold",
    pad=15
)

ax5.set_xlabel("")
ax5.set_ylabel("Number of Places")

# Add values above bars
for container in ax5.containers:
    ax5.bar_label(container, fontsize=11)

# -----------------------------
# Chart 2
# -----------------------------

ax6 = fig.add_axes([0.54, 0.12, 0.40, 0.48])

top_places = (
    places
    .sort_values("rating", ascending=False)
    .head(8)
    .sort_values("rating", ascending=True)
)

sns.barplot(
    data=top_places,
    x="rating",
    y="place_name",
    ax=ax6
)

ax6.set_title(
    "Highest Rated Tourist Places",
    fontsize=16,
    fontweight="bold",
    pad=15
)

ax6.set_xlabel("Rating")
ax6.set_ylabel("")

ax6.set_xlim(0, 5)

plt.savefig(
    r"C:\tourism-pipeline\tourism-pipeline-janhavi-gold\dashboard\overview_dashboard.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Overview dashboard created successfully!")
print("Saved as: dashboard\\overview_dashboard.png")