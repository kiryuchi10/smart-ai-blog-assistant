-- Initial database setup for AI Blog Assistant
-- This file creates the database and basic configuration

-- Create database (if running manually)
-- CREATE DATABASE ai_blog_assistant;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE subscription_tier AS ENUM ('free', 'basic', 'premium');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'expired', 'trial');
CREATE TYPE post_status AS ENUM ('draft', 'published', 'scheduled', 'archived');
CREATE TYPE post_type AS ENUM ('article', 'how-to', 'listicle', 'opinion', 'news', 'review');
CREATE TYPE content_tone AS ENUM ('professional', 'casual', 'technical', 'conversational', 'formal');
CREATE TYPE publishing_platform AS ENUM ('wordpress', 'medium', 'twitter', 'linkedin', 'custom');
CREATE TYPE schedule_status AS ENUM ('pending', 'published', 'failed', 'cancelled');

-- Create indexes for better performance (will be added by migrations)
-- These are placeholder comments for the migration system