import os
import csv
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
import logging
import pytesseract
from PIL import Image
import cv2
import numpy as np

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'csv', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_image_file(filename: str) -> bool:
    """Check if file is an image"""
    if not filename:
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to avoid conflicts"""
    name, ext = os.path.splitext(secure_filename(original_filename))
    unique_id = str(uuid.uuid4())[:8]
    return f"{name}_{unique_id}{ext}"

def parse_csv_reviews(file_path: str) -> List[Dict[str, Any]]:
    """Parse CSV file and extract review data with enhanced validation"""
    reviews = []
    errors = []
    
    try:
        # Check file size (max 16MB)
        file_size = os.path.getsize(file_path)
        if file_size > 16 * 1024 * 1024:
            raise ValueError("Filen är för stor. Maximal storlek är 16MB.")
        
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            # Try to detect delimiter and validate CSV structure
            sample = csvfile.read(1024)
            csvfile.seek(0)
            
            if not sample.strip():
                raise ValueError("Filen är tom eller innehåller endast tomma rader.")
            
            # Detect delimiter
            delimiter = ','
            if ';' in sample and sample.count(';') > sample.count(','):
                delimiter = ';'
            elif '\t' in sample:
                delimiter = '\t'
            
            # Validate CSV structure
            try:
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                headers = reader.fieldnames
                
                if not headers:
                    raise ValueError("Ingen giltig CSV-header hittades.")
                
                # Check for potential review columns
                review_columns = ['review', 'text', 'comment', 'feedback', 'recensioner', 'kommentar', 'omdöme']
                has_review_column = any(col.lower() in [h.lower() for h in headers] for col in review_columns)
                
                if not has_review_column and len(headers) < 2:
                    logger.warning("Inga kända recensionskolumner hittades. Försöker använda första textkolumnen.")
                
            except csv.Error as e:
                raise ValueError(f"Ogiltig CSV-format: {e}")
            
            # Reset file pointer and parse reviews
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            for row_num, row in enumerate(reader, 1):
                if row_num > 1000:  # Limit to 1000 reviews for free tier
                    logger.warning(f"Reached maximum review limit, stopping at row {row_num}")
                    break
                
                try:
                    review_data = parse_review_row(row)
                    if review_data:
                        # Additional validation
                        if len(review_data['review_text']) < 3:
                            errors.append(f"Rad {row_num}: Recensionstexten är för kort")
                            continue
                        
                        if len(review_data['review_text']) > 5000:
                            errors.append(f"Rad {row_num}: Recensionstexten är för lång (max 5000 tecken)")
                            continue
                        
                        reviews.append(review_data)
                    else:
                        errors.append(f"Rad {row_num}: Ingen giltig recensionstext hittades")
                        
                except Exception as e:
                    errors.append(f"Rad {row_num}: {str(e)}")
                    continue
        
        # Log errors but don't fail completely
        if errors:
            logger.warning(f"Found {len(errors)} errors while parsing CSV:")
            for error in errors[:10]:  # Log first 10 errors
                logger.warning(f"  {error}")
            if len(errors) > 10:
                logger.warning(f"  ... and {len(errors) - 10} more errors")
        
        if not reviews:
            raise ValueError("Inga giltiga recensioner hittades i filen. Kontrollera att filen innehåller recensionstext i kolumner som 'review', 'text', 'comment' eller liknande.")
                    
    except UnicodeDecodeError:
        raise ValueError("Kan inte läsa filen. Kontrollera att den är kodad i UTF-8.")
    except Exception as e:
        logger.error(f"Error parsing CSV file {file_path}: {e}")
        raise
    
    return reviews

def parse_review_row(row: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Parse a single row from CSV and extract review information"""
    # Common column names for review text
    text_columns = ['review', 'text', 'comment', 'feedback', 'recensioner', 'kommentar', 'omdöme']
    rating_columns = ['rating', 'score', 'stars', 'betyg', 'stjärnor']
    platform_columns = ['platform', 'source', 'källa', 'plattform']
    name_columns = ['name', 'reviewer', 'customer', 'namn', 'kund']
    date_columns = ['date', 'created', 'datum', 'skapad']
    
    review_text = None
    rating = None
    platform = None
    reviewer_name = None
    review_date = None
    
    # Convert all keys to lowercase for case-insensitive matching
    row_lower = {k.lower(): v for k, v in row.items()}
    
    # Find review text
    for col in text_columns:
        if col in row_lower and row_lower[col].strip():
            review_text = row_lower[col].strip()
            break
    
    if not review_text:
        # If no specific column found, use the first non-empty column that looks like text
        for value in row_lower.values():
            if value and len(value.strip()) > 10:  # Assume review text is > 10 characters
                review_text = value.strip()
                break
    
    if not review_text:
        return None
    
    # Find rating
    for col in rating_columns:
        if col in row_lower and row_lower[col].strip():
            try:
                rating = int(float(row_lower[col]))
                break
            except (ValueError, TypeError):
                continue
    
    # Find platform
    for col in platform_columns:
        if col in row_lower and row_lower[col].strip():
            platform = row_lower[col].strip()
            break
    
    # Find reviewer name
    for col in name_columns:
        if col in row_lower and row_lower[col].strip():
            reviewer_name = row_lower[col].strip()
            break
    
    # Find review date
    for col in date_columns:
        if col in row_lower and row_lower[col].strip():
            try:
                # Try different date formats
                date_str = row_lower[col].strip()
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        review_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
            except:
                continue
            break
    
    return {
        'review_text': review_text,
        'rating': rating,
        'platform': platform or 'unknown',
        'reviewer_name': reviewer_name,
        'review_date': review_date
    }

def calculate_monthly_usage(user_id: int, db) -> int:
    """Calculate how many reviews a user has processed this month"""
    from models import Review, ReviewUpload
    from sqlalchemy import func
    
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    count = db.session.query(func.count(Review.id)).join(ReviewUpload).filter(
        ReviewUpload.user_id == user_id,
        Review.processed_at >= current_month
    ).scalar()
    
    return count or 0

def check_freemium_limit(user_id: int, new_reviews_count: int, db) -> bool:
    """Check if user can process new reviews under freemium limit"""
    from models import User
    
    user = User.query.get(user_id)
    if not user:
        return False
    
    if user.plan != 'free':
        return True  # Premium users have no limit
    
    current_usage = calculate_monthly_usage(user_id, db)
    return (current_usage + new_reviews_count) <= 100  # Free tier limit

def format_sentiment_for_display(sentiment: str) -> str:
    """Format sentiment for display in Swedish"""
    sentiment_map = {
        'positive': 'Positiv',
        'negative': 'Negativ',
        'neutral': 'Neutral'
    }
    return sentiment_map.get(sentiment, sentiment.title())

def get_sentiment_color(sentiment: str) -> str:
    """Get color for sentiment display"""
    color_map = {
        'positive': '#10B981',
        'negative': '#EF4444',
        'neutral': '#F59E0B'
    }
    return color_map.get(sentiment, '#6B7280')

def parse_text_reviews(text_input: str) -> List[Dict[str, Any]]:
    """Parse text input and convert to review data format"""
    reviews = []
    
    if not text_input or not text_input.strip():
        return reviews
    
    # Split by lines and process each review
    lines = text_input.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip very short lines (likely not reviews)
        if len(line) < 3:
            continue
        
        # Skip lines that look like headers or separators
        if line.lower().startswith(('review', 'text', 'comment', 'feedback')):
            continue
        
        # Limit to 100 reviews for free tier
        if len(reviews) >= 100:
            logger.warning(f"Reached maximum review limit (100), stopping at line {line_num}")
            break
        
        # Basic validation
        if len(line) > 5000:
            logger.warning(f"Line {line_num}: Review text too long, truncating")
            line = line[:5000]
        
        # Create review data structure
        review_data = {
            'review_text': line,
            'rating': None,  # No rating info from text input
            'platform': 'text_input',
            'reviewer_name': None,
            'review_date': datetime.now()
        }
        
        reviews.append(review_data)
    
    return reviews

def extract_text_from_image(file_path: str) -> str:
    """Extract text from image using OCR with enhanced error handling"""
    try:
        # Check file size (max 5MB for OCR)
        file_size = os.path.getsize(file_path)
        if file_size > 5 * 1024 * 1024:
            raise ValueError("Bilden är för stor. Maximal storlek för OCR är 5MB.")
        
        # Open and preprocess the image
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError("Kunde inte läsa bildfilen. Kontrollera att det är en giltig bildfil.")
        
        # Check image dimensions (avoid extremely large images)
        height, width = image.shape[:2]
        if width > 4000 or height > 4000:
            # Resize large images to improve processing speed
            scale = min(4000/width, 4000/height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply image preprocessing to improve OCR accuracy
        # Remove noise
        denoised = cv2.medianBlur(gray, 3)
        
        # Apply threshold to get better text extraction
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Use Tesseract to extract text - optimized for Swedish and English
        custom_config = r'--oem 3 --psm 6 -l swe+eng'
        extracted_text = pytesseract.image_to_string(thresh, config=custom_config)
        
        if not extracted_text.strip():
            # Try with different PSM mode for complex layouts
            custom_config = r'--oem 3 --psm 3 -l swe+eng'
            extracted_text = pytesseract.image_to_string(thresh, config=custom_config)
        
        if not extracted_text.strip():
            # Final attempt with different preprocessing
            # Apply morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            custom_config = r'--oem 3 --psm 11 -l swe+eng'
            extracted_text = pytesseract.image_to_string(processed, config=custom_config)
        
        # Clean up the extracted text
        cleaned_text = extracted_text.strip()
        
        # Validate that we have meaningful text
        if not cleaned_text:
            raise ValueError("Ingen text hittades i bilden. Kontrollera att bilden innehåller tydlig text.")
        
        if len(cleaned_text) < 5:
            raise ValueError("För lite text hittades. Försök med en tydligare bild med mer text.")
        
        # Check if text looks like meaningful content (not just random characters)
        import re
        words = re.findall(r'\b[a-zA-ZåäöÅÄÖ]{2,}\b', cleaned_text)
        if len(words) < 3:
            raise ValueError("Texten verkar inte innehålla meningsfulla ord. Försök med en annan bild.")
        
        logger.info(f"Successfully extracted {len(cleaned_text)} characters and {len(words)} words from image")
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Error extracting text from image {file_path}: {e}")
        if "Ingen text hittades" in str(e) or "För lite text" in str(e) or "meningsfulla ord" in str(e):
            raise
        else:
            raise ValueError("Ett fel uppstod vid textextrahering. Kontrollera att bilden är tydlig och innehåller text.")

def parse_image_reviews(file_path: str) -> List[Dict[str, Any]]:
    """Extract text from image and convert to review data format"""
    try:
        # Extract text from image
        extracted_text = extract_text_from_image(file_path)
        
        if not extracted_text or len(extracted_text.strip()) < 5:
            raise ValueError("För lite text hittades i bilden för att kunna analysera")
        
        # Split text into potential reviews (by lines, sentences, or paragraphs)
        reviews = []
        
        # Try to identify separate reviews in the extracted text
        # Split by double newlines first (paragraphs)
        paragraphs = extracted_text.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if len(para) < 10:  # Skip very short texts
                continue
            
            # Further split long paragraphs by sentences if they're too long
            if len(para) > 1000:
                sentences = para.split('. ')
                current_review = ""
                
                for sentence in sentences:
                    if len(current_review + sentence) > 500:
                        if current_review.strip():
                            reviews.append({
                                'review_text': current_review.strip(),
                                'rating': None,
                                'platform': 'image_ocr',
                                'reviewer_name': None,
                                'review_date': datetime.now()
                            })
                        current_review = sentence
                    else:
                        current_review += sentence + ". "
                
                if current_review.strip():
                    reviews.append({
                        'review_text': current_review.strip(),
                        'rating': None,
                        'platform': 'image_ocr',
                        'reviewer_name': None,
                        'review_date': datetime.now()
                    })
            else:
                reviews.append({
                    'review_text': para,
                    'rating': None,
                    'platform': 'image_ocr',
                    'reviewer_name': None,
                    'review_date': datetime.now()
                })
        
        # If no good paragraphs found, treat entire text as one review
        if not reviews:
            reviews.append({
                'review_text': extracted_text.strip(),
                'rating': None,
                'platform': 'image_ocr',
                'reviewer_name': None,
                'review_date': datetime.now()
            })
        
        # Limit to prevent abuse
        if len(reviews) > 50:
            reviews = reviews[:50]
            logger.warning("Limited OCR results to 50 reviews")
        
        return reviews
        
    except Exception as e:
        logger.error(f"Error processing image {file_path}: {e}")
        raise

def ensure_upload_directory():
    """Ensure upload directory exists"""
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    reports_dir = os.path.join('static', 'reports')
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

def clean_old_files(max_age_days: int = 7):
    """Clean old uploaded files and reports"""
    import time
    
    directories = ['uploads', os.path.join('static', 'reports')]
    current_time = time.time()
    
    for directory in directories:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > (max_age_days * 24 * 60 * 60):
                        try:
                            os.remove(file_path)
                            logger.info(f"Removed old file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error removing file {file_path}: {e}")
