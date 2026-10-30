import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DB_PATH = r"data\gold\goa_tourism.duckdb"

con = duckdb.connect(DB_PATH, read_only=True)

places = con.sql("""
    SELECT
        place_name,
        rating,
        review_count_lakhs,
        entrance_fee_inr,
        is_outdoor
    FROM dim_place
    ORDER BY rating DESC
""").df()

con.close()

sns.set_theme(style="whitegrid")

fig, axes = plt.subplots(2, 2, figsize=(16, 11))

# 1. Ratings
sns.barplot(
    data=places,
    x="rating",
    y="place_name",
    ax=axes[0, 0]
)

axes[0, 0].set_title("Tourist Places by Rating")
axes[0, 0].set_xlabel("Rating")
axes[0, 0].set_ylabel("Tourist Place")

# 2. Reviews
reviews = places.sort_values("review_count_lakhs", ascending=False)

sns.barplot(
    data=reviews,
    x="review_count_lakhs",
    y="place_name",
    ax=axes[0, 1]
)

axes[0, 1].set_title("Tourist Places by Reviews")
axes[0, 1].set_xlabel("Reviews (Lakhs)")
axes[0, 1].set_ylabel("Tourist Place")

# 3. Entrance Fees
fees = places.sort_values("entrance_fee_inr", ascending=False)

sns.barplot(
    data=fees,
    x="entrance_fee_inr",
    y="place_name",
    ax=axes[1, 0]
)

axes[1, 0].set_title("Entrance Fee by Tourist Place")
axes[1, 0].set_xlabel("Entrance Fee (INR)")
axes[1, 0].set_ylabel("Tourist Place")

# 4. Outdoor vs Indoor
outdoor_counts = (
    places["is_outdoor"]
    .map({True: "Outdoor", False: "Indoor"})
    .value_counts()
    .reset_index()
)

outdoor_counts.columns = ["Type", "Places"]

sns.barplot(
    data=outdoor_counts,
    x="Type",
    y="Places",
    ax=axes[1, 1]
)

axes[1, 1].set_title("Outdoor vs Indoor Tourist Places")
axes[1, 1].set_xlabel("Place Type")
axes[1, 1].set_ylabel("Number of Places")

plt.suptitle(
    "Goa Tourism Analytics - Tourist Places Analysis",
    fontsize=18,
    fontweight="bold"
)

plt.tight_layout()

output_path = "dashboard\\tourist_places_dashboard.png"

plt.savefig(output_path, dpi=300, bbox_inches="tight")

plt.close()

print("Tourist Places dashboard created successfully!")
print(f"Saved as: {output_path}")