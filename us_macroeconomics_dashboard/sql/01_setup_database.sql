-- =============================================================
-- 01_setup_database.sql
-- Creates the application database, schema, and CRUD table
-- for the US Macro Economic Observatory app.
-- =============================================================

USE ROLE ACCOUNTADMIN;

-- Application database
CREATE DATABASE IF NOT EXISTS HACKDAYS_APP_DB;

-- Schema for app-managed objects
CREATE SCHEMA IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA;

-- Watchlist: user-created tracked entities (full CRUD)
CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.WATCHLIST (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    ENTITY_TYPE    VARCHAR(30)   NOT NULL,
    ENTITY_NAME    VARCHAR(500)  NOT NULL,
    TARGET_VALUE   FLOAT,
    NOTES          VARCHAR(2000),
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Chat history: persists AI assistant conversations
CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.CHAT_HISTORY (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    SESSION_ID     VARCHAR(100)  NOT NULL,
    ROLE           VARCHAR(20)   NOT NULL,
    CONTENT        VARCHAR(16000),
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Insights log: stores generated analytical insights for audit
CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.INSIGHTS_LOG (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    INSIGHT_TYPE   VARCHAR(50)   NOT NULL,
    INSIGHT_TEXT   VARCHAR(8000) NOT NULL,
    DATA_SNAPSHOT  VARIANT,
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
