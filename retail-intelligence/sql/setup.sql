-- ============================================================
-- Retail Intelligence — Snowflake Setup Script
-- ============================================================
-- Run this script to reproduce the Snowflake project from scratch.
-- SAFE: Does NOT drop existing tables/views unless told to.
-- ============================================================


-- ── Database & Schema ───────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS RETAIL_INTELLIGENCE_DB;

USE DATABASE RETAIL_INTELLIGENCE_DB;

CREATE SCHEMA IF NOT EXISTS RETAIL;

USE SCHEMA RETAIL;


-- ── Tables ──────────────────────────────────────────────────────────────────

-- Customers
CREATE TABLE IF NOT EXISTS CUSTOMERS (
    CUSTOMER_ID     INT PRIMARY KEY,
    CUSTOMER_NAME   VARCHAR(100) NOT NULL,
    EMAIL           VARCHAR(150),
    COUNTRY         VARCHAR(50)  NOT NULL,
    CREATED_AT      DATE
);

-- Products
CREATE TABLE IF NOT EXISTS PRODUCTS (
    PRODUCT_ID      INT PRIMARY KEY,
    PRODUCT_NAME    VARCHAR(150) NOT NULL,
    CATEGORY        VARCHAR(50)  NOT NULL,
    PRICE           DECIMAL(10, 2) NOT NULL,
    STOCK           INT DEFAULT 0
);

-- Orders
CREATE TABLE IF NOT EXISTS ORDERS (
    ORDER_ID        INT PRIMARY KEY,
    CUSTOMER_ID     INT REFERENCES CUSTOMERS(CUSTOMER_ID),
    PRODUCT_ID      INT REFERENCES PRODUCTS(PRODUCT_ID),
    ORDER_DATE      DATE NOT NULL,
    QUANTITY        INT NOT NULL,
    TOTAL_AMOUNT    DECIMAL(10, 2) NOT NULL
);


-- ── Sample Data ─────────────────────────────────────────────────────────────

-- Customers
INSERT INTO CUSTOMERS (CUSTOMER_ID, CUSTOMER_NAME, EMAIL, COUNTRY, CREATED_AT) VALUES
(1,  'Aanya Sharma',    'aanya@example.com',    'India',          '2023-01-10'),
(2,  'James Carter',    'james@example.com',    'United States',  '2023-02-14'),
(3,  'Li Wei',          'liwei@example.com',    'China',          '2023-03-05'),
(4,  'Fatima Al-Said',  'fatima@example.com',   'UAE',            '2023-03-22'),
(5,  'Carlos Rivera',   'carlos@example.com',   'Brazil',         '2023-04-01'),
(6,  'Sophie Martin',   'sophie@example.com',   'France',         '2023-04-18'),
(7,  'Kenji Tanaka',    'kenji@example.com',    'Japan',          '2023-05-09'),
(8,  'Priya Nair',      'priya@example.com',    'India',          '2023-05-20'),
(9,  'Ahmed Hassan',    'ahmed@example.com',    'Egypt',          '2023-06-03'),
(10, 'Emma Wilson',     'emma@example.com',     'United Kingdom', '2023-06-15');

-- Products
INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, CATEGORY, PRICE, STOCK) VALUES
(1,  'UltraBook Pro 15',        'Electronics',   1299.99,  45),
(2,  'Wireless Noise Cancelling Headphones', 'Electronics', 249.99, 180),
(3,  'Running Shoes X9',        'Sports',         89.99,  320),
(4,  'Yoga Mat Premium',        'Sports',         34.99,   80),
(5,  'Python Programming Guide','Books',          29.99,  500),
(6,  'Data Science Handbook',   'Books',          39.99,  310),
(7,  'Smart Watch Series 5',    'Electronics',   399.99,   60),
(8,  'Resistance Bands Set',    'Sports',         19.99,   95),
(9,  'Business Strategy 101',   'Books',          24.99,  420),
(10, '4K Gaming Monitor 27"',   'Electronics',   699.99,   30),
(11, 'Cotton T-Shirt Pack',     'Apparel',        24.99,  600),
(12, 'Denim Jacket Classic',    'Apparel',        79.99,  140),
(13, 'Ceramic Coffee Mug Set',  'Home & Kitchen', 19.99,  250),
(14, 'Non-Stick Cookware Set',  'Home & Kitchen', 89.99,   70),
(15, 'Standing Desk Adjustable','Home & Kitchen', 349.99,  25);

-- Orders
INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, PRODUCT_ID, ORDER_DATE, QUANTITY, TOTAL_AMOUNT) VALUES
(1001, 1,  1,  '2024-01-05', 1, 1299.99),
(1002, 2,  2,  '2024-01-08', 2,  499.98),
(1003, 3,  5,  '2024-01-12', 3,   89.97),
(1004, 4,  7,  '2024-01-15', 1,  399.99),
(1005, 5,  3,  '2024-01-20', 2,  179.98),
(1006, 6,  6,  '2024-01-22', 1,   39.99),
(1007, 7, 10,  '2024-01-28', 1,  699.99),
(1008, 8,  4,  '2024-02-01', 2,   69.98),
(1009, 9,  9,  '2024-02-05', 1,   24.99),
(1010, 10, 11,  '2024-02-10', 3,   74.97),
(1011, 1,  2,  '2024-02-14', 1,  249.99),
(1012, 2,  8,  '2024-02-18', 4,   79.96),
(1013, 3, 12,  '2024-02-22', 1,   79.99),
(1014, 4, 13,  '2024-02-25', 2,   39.98),
(1015, 5,  1,  '2024-03-01', 1, 1299.99),
(1016, 6, 14,  '2024-03-04', 1,   89.99),
(1017, 7,  5,  '2024-03-08', 5,  149.95),
(1018, 8,  7,  '2024-03-12', 1,  399.99),
(1019, 9, 15,  '2024-03-15', 1,  349.99),
(1020, 10, 3,  '2024-03-20', 2,  179.98),
(1021, 1,  6,  '2024-03-25', 2,   79.98),
(1022, 2, 10,  '2024-03-28', 1,  699.99),
(1023, 3,  4,  '2024-04-02', 3,  104.97),
(1024, 4, 11,  '2024-04-05', 4,   99.96),
(1025, 5,  9,  '2024-04-10', 2,   49.98),
(1026, 6,  2,  '2024-04-14', 1,  249.99),
(1027, 7, 13,  '2024-04-18', 3,   59.97),
(1028, 8,  1,  '2024-04-22', 1, 1299.99),
(1029, 9, 12,  '2024-04-26', 2,  159.98),
(1030, 10, 7,  '2024-04-30', 1,  399.99);


-- ── View ─────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW RETAIL_SALES AS
    SELECT
        o.ORDER_ID,
        o.ORDER_DATE,
        o.QUANTITY,
        o.TOTAL_AMOUNT,
        c.CUSTOMER_ID,
        c.CUSTOMER_NAME,
        c.COUNTRY,
        p.PRODUCT_ID,
        p.PRODUCT_NAME,
        p.CATEGORY,
        p.PRICE
    FROM ORDERS         o
    JOIN CUSTOMERS      c ON o.CUSTOMER_ID = c.CUSTOMER_ID
    JOIN PRODUCTS       p ON o.PRODUCT_ID  = p.PRODUCT_ID;


-- ── Verify ───────────────────────────────────────────────────────────────────

SELECT 'CUSTOMERS' AS tbl, COUNT(*) AS rows FROM CUSTOMERS
UNION ALL
SELECT 'PRODUCTS',          COUNT(*) FROM PRODUCTS
UNION ALL
SELECT 'ORDERS',            COUNT(*) FROM ORDERS
UNION ALL
SELECT 'RETAIL_SALES (view)', COUNT(*) FROM RETAIL_SALES;
