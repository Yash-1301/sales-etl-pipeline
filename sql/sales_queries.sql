-- sales_queries.sql
-- Comments explain the purpose of each analytical block.

-- =========================================================
-- 1. CATEGORY PERFORMANCE (Revenues, Costs, Profit, Margin)
-- =========================================================
-- This query joins fact_sales with dim_products to evaluate which product categories
-- generate the highest revenues, net profits, and profit margins.
SELECT
    p.category,
    p.sub_category,
    COUNT(DISTINCT f.order_id) as total_orders,
    SUM(f.quantity) as total_quantity_sold,
    ROUND(SUM(f.gross_revenue), 2) as gross_revenue,
    ROUND(SUM(f.discount_amount), 2) as total_discounts_given,
    ROUND(SUM(f.net_revenue), 2) as net_revenue,
    ROUND(SUM(f.total_cost), 2) as total_manufacturing_cost,
    ROUND(SUM(f.net_profit), 2) as net_profit,
    ROUND((SUM(f.net_profit) / SUM(f.net_revenue)) * 100, 2) as overall_profit_margin_pct
FROM fact_sales f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.category, p.sub_category
ORDER BY net_profit DESC;


-- =========================================================
-- 2. MONTH-OVER-MONTH (MoM) SALES REVENUE TREND
-- =========================================================
-- Evaluates sales growth trends. It joins the fact table with dim_date to group by
-- Year and Month, then uses the LAG() window function to calculate the MoM growth rate.
WITH monthly_revenue AS (
    SELECT
        d.year,
        d.month,
        d.month_name,
        ROUND(SUM(f.net_revenue), 2) as net_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.order_date_key = d.date_key
    GROUP BY d.year, d.month, d.month_name
)
SELECT
    year,
    month_name,
    net_revenue,
    LAG(net_revenue) OVER (ORDER BY year, month) as prev_month_revenue,
    ROUND(
        (net_revenue - LAG(net_revenue) OVER (ORDER BY year, month)) / 
        LAG(net_revenue) OVER (ORDER BY year, month) * 100, 
        2
    ) as mom_growth_pct
FROM monthly_revenue
ORDER BY year, month;


-- =========================================================
-- 3. DISCOUNT VS. MARGIN IMPACT ANALYSIS
-- =========================================================
-- Evaluates the business hypothesis: "High discount rates destroy net profit margin."
-- This query breaks down the sales performance across different discount rates.
SELECT
    discount as discount_rate,
    COUNT(*) as total_order_items,
    SUM(quantity) as total_quantity,
    ROUND(SUM(gross_revenue), 2) as gross_revenue,
    ROUND(SUM(net_revenue), 2) as net_revenue,
    ROUND(SUM(net_profit), 2) as net_profit,
    ROUND((SUM(net_profit) / SUM(f.net_revenue)) * 100, 2) as profit_margin_pct
FROM fact_sales f
GROUP BY discount
ORDER BY discount ASC;


-- =========================================================
-- 4. CUSTOMER SEGMENT & GEOGRAPHY PERFORMANCE
-- =========================================================
-- Evaluates revenue contributions across B2C/B2B customer segments and countries.
SELECT
    c.segment,
    c.country,
    COUNT(DISTINCT f.order_id) as total_orders,
    ROUND(SUM(f.net_revenue), 2) as net_revenue,
    ROUND(SUM(f.net_profit), 2) as net_profit,
    ROUND((SUM(f.net_profit) / SUM(f.net_revenue)) * 100, 2) as profit_margin_pct
FROM fact_sales f
JOIN dim_customers c ON f.customer_id = c.customer_id
GROUP BY c.segment, c.country
ORDER BY net_revenue DESC;


-- =========================================================
-- 5. ETL HEALTH CHECK LOGS
-- =========================================================
-- Queries the metadata etl_log table to verify the details and health of pipeline runs.
SELECT
    run_id,
    run_timestamp,
    status,
    extracted_files,
    records_loaded,
    ROUND(execution_time_sec, 4) as execution_time_sec,
    error_message
FROM etl_log
ORDER BY run_id DESC;
