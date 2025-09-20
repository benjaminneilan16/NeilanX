# Overview

NeilanX is a Swedish AI-powered customer review analysis platform designed for small e-commerce businesses. The application processes customer reviews from various platforms (Google Reviews, Trustpilot, Shopify) and provides automated sentiment analysis, keyword extraction, and comprehensive reporting. Built with Flask and featuring a freemium business model, it targets Swedish e-commerce companies that need to understand customer feedback efficiently without manual analysis.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The application uses a traditional server-side rendering approach with Flask templates and Jinja2. The frontend is built with:
- **Bootstrap 5** for responsive UI components and layout
- **Font Awesome** icons for visual elements
- **Chart.js** for data visualization (sentiment charts, trend analysis)
- **Custom CSS** with CSS variables for consistent branding
- **Vanilla JavaScript** for interactive features like file uploads and dashboard functionality

## Backend Architecture
The backend follows a monolithic Flask architecture with clear separation of concerns:
- **Flask** as the main web framework with SQLAlchemy ORM
- **Route-based architecture** with dedicated modules for different functionalities
- **Session-based authentication** using Flask sessions
- **File upload handling** with security validation and unique filename generation
- **Background processing** capability for review analysis (status tracking: pending, processing, completed, failed)

## Data Storage Solutions
The application uses **SQLAlchemy** with a relational database design:
- **Users table** - stores user accounts with freemium plan tracking
- **ReviewUploads table** - tracks file uploads and processing status
- **Reviews table** - stores individual reviews with sentiment analysis results
- **Reports table** - manages generated PDF reports (schema appears incomplete)
- **Database connection pooling** configured for production reliability

## Authentication and Authorization
- **Session-based authentication** using Flask sessions
- **Simple email-based user registration** without complex password requirements
- **Plan-based access control** (free vs premium) with usage limits
- **Freemium limitations** enforced at the business logic level

## AI and Analytics Engine
- **Transformers-based sentiment analysis** using Hugging Face models
- **Multi-language support** with Swedish-specific models (KBLab/bert-base-swedish-cased)
- **Fallback model strategy** for robustness
- **Text preprocessing** for Swedish language optimization
- **Keyword extraction** and sentiment scoring (0-1 confidence scale)

## Report Generation System
- **ReportLab-based PDF generation** with custom styling
- **Chart integration** using pie charts and bar charts for visual data representation
- **Template-based reports** with consistent branding
- **File storage** in local upload directories

## File Processing Pipeline
- **CSV parsing** with automatic delimiter detection
- **Security validation** for file types and sizes (16MB limit)
- **Batch processing** with progress tracking
- **Error handling** for malformed data
- **Usage quota enforcement** for freemium users (100 reviews/month limit)

# External Dependencies

## AI/ML Services
- **Hugging Face Transformers** - Primary sentiment analysis models
- **PyTorch** - Machine learning framework for model execution
- **KBLab Swedish BERT** - Swedish language sentiment analysis
- **Cardiff NLP RoBERTa** - Fallback English sentiment model

## Frontend Libraries
- **Bootstrap 5** (CDN) - UI framework and responsive design
- **Font Awesome 6** (CDN) - Icon library
- **Chart.js** (CDN) - Data visualization charts

## Backend Dependencies
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Werkzeug** - WSGI utilities and security
- **ReportLab** - PDF generation library

## File Processing
- **CSV parsing** - Built-in Python csv module
- **Werkzeug file handling** - Secure file upload processing

## Database
- **SQLAlchemy** - Currently database-agnostic, can be configured for PostgreSQL, MySQL, or SQLite via DATABASE_URL environment variable

## Hosting and Deployment
- **Environment variable configuration** for database connections and session secrets
- **ProxyFix middleware** configured for HTTPS deployment
- **File upload directory management** with automatic creation

# Recent Updates - August 27, 2025

## Latest UI & Pricing Updates

### ✅ Pricing Strategy Refinement
- **Konsultpaket pricing updated**: Changed from fixed "1 999 kr/projekt" to "Anpassad" (customized pricing)
- Updated pricing description: "Per projekt" → "Kostnad efter behov"
- Live chat updated to reflect flexible consultation pricing model
- Emphasizes personalized approach for enterprise customers requiring custom solutions

### ✅ User Interface Consistency
- **CSV Guide branding restored**: Reverted "steg-för-steg guide" back to "videoguide" terminology
- Maintained video icons and 2-minute timing indication for user familiarity
- Updated all references across upload page, modals, and live chat responses
- Preserved existing interactive guide functionality while keeping recognizable branding

### ✅ Platform Status
- All pricing tiers clearly differentiated: Free (100 reviews), Premium (399 kr/month), Konsultpaket (customized)
- Interactive guide system fully functional with proper video-style branding
- Live chat responses accurate for all pricing and feature inquiries

# Previous Updates - August 22, 2025

## Major Platform Improvements

### ✅ Technical Fixes & Stability
- Fixed all critical coding errors and variable scope issues in file upload handling
- Improved error handling and memory management for image processing
- Enhanced GDPR compliance with proper file cleanup after OCR processing
- Eliminated all diagnostic errors for more stable code execution

### ✅ New User Experience Features
- **Guided Tutorial System**: Interactive 4-step tutorial for new Swedish e-commerce users
- Auto-detection of first-time users with automatic tutorial activation
- Manual tutorial trigger option with `?tutorial=true` URL parameter
- Professional modal overlay with Swedish language content
- Step-by-step guidance for CSV uploads, text input, and OCR image processing

### ✅ Website Content Improvements
- Enhanced platform with OCR functionality using Tesseract for extracting text from images
- Updated website branding: changed "Integrationer" to "Flexibel inmatning"
- Fixed misleading text about "automatic" Google/Trustpilot integration to reflect manual upload requirement
- Removed stock image and improved website accuracy about platform capabilities
- Clarified platform architecture: completely local processing with no external API dependencies

### ✅ Account Management
- Upgraded user account (benjaneilan@icloud.com) to Premium plan for testing
- Premium features: unlimited reviews, detailed reports, advanced analytics

### ✅ Platform Status
- All systems operational and error-free
- Tutorial system ready for new Swedish e-commerce users
- Database and models properly configured with relationships
- Server running smoothly on port 5000