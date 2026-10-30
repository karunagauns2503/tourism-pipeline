-- Goa Tourism Analytics: Gold layer views
-- Tables: fact_daily_weather, dim_date, dim_rain_category, dim_place

-- 1. Rain and temperature by month
CREATE VIEW v_monthly_weather AS
SELECT d.year, d.month, d.month_name,
       round(sum(f.rainfall_mm),1) AS total_rain_mm,
       count(*) FILTER (WHERE f.rainfall_mm >= 2.5) AS rainy_days,
       round(avg(f.max_temp_c),1) AS avg_max_temp_c
FROM fact_daily_weather f JOIN dim_date d USING (date_key)
GROUP BY 1,2,3 ORDER BY 1,2;

-- 2. Weather by season
CREATE VIEW v_season_weather AS
SELECT d.season, count(*) AS days,
       round(avg(f.rainfall_mm),2) AS avg_daily_rain_mm,
       count(*) FILTER (WHERE c.category_name = 'Heavy Monsoon') AS heavy_rain_days,
       round(avg(f.max_temp_c),1) AS avg_max_temp_c
FROM fact_daily_weather f JOIN dim_date d USING (date_key)
JOIN dim_rain_category c USING (category_key)
GROUP BY 1 ORDER BY 3 DESC;

-- 3. Weather on each holiday
CREATE VIEW v_holiday_weather AS
SELECT d.date, d.holiday_name, d.is_long_weekend, d.season,
       f.rainfall_mm, c.category_name AS rain_category
FROM fact_daily_weather f JOIN dim_date d USING (date_key)
JOIN dim_rain_category c USING (category_key)
WHERE d.is_holiday ORDER BY d.date;

-- 4. How many holiday days fall in each rain category
CREATE VIEW v_holidays_by_rain AS
SELECT c.category_name AS rain_category, count(*) AS holiday_days
FROM fact_daily_weather f JOIN dim_date d USING (date_key)
JOIN dim_rain_category c USING (category_key)
WHERE d.is_holiday GROUP BY 1;

-- 5. Outdoor vs indoor Goa places
CREATE VIEW v_place_summary AS
SELECT is_outdoor, count(*) AS places,
       round(avg(rating),2) AS avg_rating,
       round(avg(review_count_lakhs),2) AS avg_reviews_lakhs,
       round(avg(entrance_fee_inr),0) AS avg_fee_inr
FROM dim_place GROUP BY is_outdoor;