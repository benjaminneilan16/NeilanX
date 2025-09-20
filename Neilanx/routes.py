import os
import json
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.utils import secure_filename
from app import app, db
from models import User, ReviewUpload, Review, Report
from sentiment_analyzer import sentiment_analyzer
from pdf_generator import report_generator
from utils import (
    allowed_file, generate_unique_filename, parse_csv_reviews, parse_text_reviews,
    check_freemium_limit, ensure_upload_directory, format_sentiment_for_display,
    get_sentiment_color, is_image_file, parse_image_reviews
)
from sample_reviews_demo import get_demo_reviews, get_demo_csv_content

logger = logging.getLogger(__name__)

# Initialize email service
try:
    from email_service import init_mail, send_report_notification
    mail = init_mail(app)
    EMAIL_ENABLED = True
except ImportError as e:
    mail = None
    EMAIL_ENABLED = False
    send_report_notification = lambda *args, **kwargs: False  # Dummy function
    logger.warning(f"Email service not available: {e}")

# Ensure upload directories exist
ensure_upload_directory()

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    message_sent = False
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        company = request.form.get('company', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        newsletter = request.form.get('newsletter') == 'on'
        
        # Basic validation
        if name and email and subject and message:
            # In a real application, you would send an email or save to database
            # For now, we'll just log it and show a success message
            logger.info(f"Contact form submission: {name} ({email}) - {subject}")
            message_sent = True
            flash('Tack för ditt meddelande! Vi återkommer inom 24 timmar.', 'success')
        else:
            flash('Vänligen fyll i alla obligatoriska fält.', 'error')
    
    return render_template('contact.html', message_sent=message_sent)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        company_name = request.form.get('company_name', '').strip()
        
        if not email or not company_name:
            flash('E-post och företagsnamn krävs.', 'error')
            return redirect(url_for('register'))
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('En användare med denna e-post finns redan.', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User()
        user.email = email
        user.company_name = company_name
        db.session.add(user)
        db.session.commit()
        
        # Store user ID in session
        session['user_id'] = user.id
        flash('Konto skapat! Välkommen till NeilanX.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('E-post krävs.', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Ingen användare hittades med denna e-post.', 'error')
            return redirect(url_for('login'))
        
        session['user_id'] = user.id
        flash('Inloggad!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.pop('user_id', None)
    flash('Du har loggats ut.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Du måste logga in för att komma åt dashboarden.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('Användare hittades inte.', 'error')
        return redirect(url_for('login'))
    
    # Get user's uploads
    uploads = ReviewUpload.query.filter_by(user_id=user_id).order_by(ReviewUpload.upload_date.desc()).all()
    
    # Get recent reviews for dashboard
    recent_reviews = []
    sentiment_summary = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    if uploads:
        # Get reviews from latest upload
        latest_upload = uploads[0]
        recent_reviews = Review.query.filter_by(upload_id=latest_upload.id).limit(10).all()
        
        # Calculate sentiment summary from all user's reviews
        all_reviews = db.session.query(Review).join(ReviewUpload).filter(
            ReviewUpload.user_id == user_id
        ).all()
        
        for review in all_reviews:
            sentiment = review.sentiment or 'neutral'
            sentiment_summary[sentiment] += 1
    
    return render_template('dashboard.html', 
                         user=user, 
                         uploads=uploads, 
                         recent_reviews=recent_reviews,
                         sentiment_summary=sentiment_summary,
                         format_sentiment=format_sentiment_for_display,
                         get_sentiment_color=get_sentiment_color)

@app.route('/upload', methods=['GET', 'POST'])
def upload_reviews():
    """Upload and process reviews"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Du måste logga in för att ladda upp recensioner.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('Användare hittades inte.', 'error')
        return redirect(url_for('login'))
    
    # Check state BEFORE any mutations
    has_uploads = ReviewUpload.query.filter_by(user_id=user_id).first() is not None
    show_tutorial_manually = request.args.get('tutorial') == 'true'
    is_first_visit = user.first_login
    onboarding_incomplete = not user.onboarding_completed
    
    # Determine what to show with mutual exclusion
    # Priority: manual tutorial > existing tutorial > onboarding modal
    if show_tutorial_manually:
        show_tutorial = True
        show_onboarding_modal = False
    elif not has_uploads and onboarding_incomplete:
        # First-time user with no uploads - use existing tutorial system
        show_tutorial = True
        show_onboarding_modal = False
    elif is_first_visit and onboarding_incomplete:
        # First visit but has some experience - use modal
        show_tutorial = False
        show_onboarding_modal = True
    else:
        # Experienced user
        show_tutorial = False
        show_onboarding_modal = False
    
    if request.method == 'POST':
        # Check if this is text input, image upload, or CSV file upload
        input_type = request.form.get('input_type', 'file')
        
        if input_type == 'text':
            # Handle text input
            reviews_text = request.form.get('reviews_text', '').strip()
            if not reviews_text:
                flash('Ingen text angavs. Klistra in eller skriv recensioner.', 'error')
                return redirect(request.url)
            
            try:
                # Parse text input into review data
                reviews_data = parse_text_reviews(reviews_text)
                
                if not reviews_data:
                    flash('Inga giltiga recensioner hittades i texten.', 'error')
                    return redirect(request.url)
                
                # Check freemium limits
                if not check_freemium_limit(user_id, len(reviews_data), db):
                    flash(f'Freemium-gränsen (100 recensioner/månad) överskrids. Du försöker analysera {len(reviews_data)} recensioner.', 'error')
                    return redirect(url_for('pricing'))
                
                # Process text reviews directly (no file to save)
                upload = ReviewUpload()
                upload.user_id = user_id
                upload.filename = f"text_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                upload.total_reviews = len(reviews_data)
                upload.status = 'processing'
                db.session.add(upload)
                db.session.commit()
                
                # Process reviews with sentiment analysis
                processed_count = 0
                for review_data in reviews_data:
                    try:
                        # Perform sentiment analysis
                        sentiment_result = sentiment_analyzer.analyze_sentiment(review_data['review_text'])
                        keywords = sentiment_analyzer.extract_keywords(review_data['review_text'])
                        
                        # Create review record
                        review = Review()
                        review.upload_id = upload.id
                        review.review_text = review_data['review_text']
                        review.rating = review_data.get('rating')
                        review.platform = review_data.get('platform', 'text_input')
                        review.reviewer_name = review_data.get('reviewer_name')
                        review.review_date = review_data.get('review_date')
                        review.sentiment = sentiment_result['sentiment']
                        review.sentiment_score = sentiment_result['score']
                        review.keywords = json.dumps(keywords, ensure_ascii=False)
                        db.session.add(review)
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing review: {e}")
                        continue
                
                # Update upload status
                upload.processed_reviews = processed_count
                upload.status = 'completed' if processed_count > 0 else 'failed'
                db.session.commit()
                
                if processed_count > 0:
                    flash(f'Framgångsrikt analyserade {processed_count} recensioner!', 'success')
                    return redirect(url_for('dashboard', upload_id=upload.id))
                else:
                    flash('Inga recensioner kunde bearbetas.', 'error')
                    
            except Exception as e:
                logger.error(f"Error processing text input: {e}")
                flash('Ett fel uppstod vid bearbetning av texten.', 'error')
                return redirect(request.url)
        
        elif input_type == 'image':
            # Handle image upload with OCR
            if 'file' not in request.files:
                flash('Ingen bildfil valdes.', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('Ingen bildfil valdes.', 'error')
                return redirect(request.url)
            
            if not file.filename or not is_image_file(file.filename):
                flash('Endast bildfiler (PNG, JPG, JPEG, GIF, BMP, TIFF) är tillåtna för OCR-analys.', 'error')
                return redirect(request.url)
            
            # Check GDPR consent
            gdpr_consent = request.form.get('gdpr_consent')
            if not gdpr_consent:
                flash('Du måste ge samtycke för att vi ska kunna bearbeta bilden enligt GDPR.', 'error')
                return redirect(request.url)
            
            # Initialize variables for error handling
            file_path = None
            filename = None
            
            try:
                # Save uploaded image temporarily
                filename = generate_unique_filename(file.filename)
                file_path = os.path.join('uploads', filename)
                file.save(file_path)
                
                # Check file size before processing
                file_size = os.path.getsize(file_path)
                if file_size > 5 * 1024 * 1024:  # 5MB limit
                    os.remove(file_path)
                    flash('Bilden är för stor. Maximal storlek är 5MB för OCR-bearbetning.', 'error')
                    return redirect(request.url)
                
                # Extract text from image using OCR
                reviews_data = parse_image_reviews(file_path)
                
                # Immediately delete the image file for GDPR compliance
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted uploaded image {filename} for GDPR compliance")
                
                if not reviews_data:
                    flash('Ingen användbar text kunde extraheras från bilden. Försök med en tydligare skärmdump.', 'error')
                    return redirect(request.url)
                
                # Check freemium limits
                if not check_freemium_limit(user_id, len(reviews_data), db):
                    flash(f'Freemium-gränsen (100 recensioner/månad) överskrids. Extraherade {len(reviews_data)} textdelar från bilden.', 'error')
                    os.remove(file_path)
                    return redirect(url_for('pricing'))
                
                # Process OCR extracted reviews
                upload = ReviewUpload()
                upload.user_id = user_id
                upload.filename = f"ocr_{file.filename}"
                upload.total_reviews = len(reviews_data)
                upload.status = 'processing'
                db.session.add(upload)
                db.session.commit()
                
                # Process reviews with sentiment analysis
                processed_count = 0
                for review_data in reviews_data:
                    try:
                        # Perform sentiment analysis
                        sentiment_result = sentiment_analyzer.analyze_sentiment(review_data['review_text'])
                        keywords = sentiment_analyzer.extract_keywords(review_data['review_text'])
                        
                        # Create review record
                        review = Review()
                        review.upload_id = upload.id
                        review.review_text = review_data['review_text']
                        review.rating = review_data.get('rating')
                        review.platform = review_data.get('platform', 'image_ocr')
                        review.reviewer_name = review_data.get('reviewer_name')
                        review.review_date = review_data.get('review_date')
                        review.sentiment = sentiment_result['sentiment']
                        review.sentiment_score = sentiment_result['score']
                        review.keywords = json.dumps(keywords, ensure_ascii=False)
                        db.session.add(review)
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing OCR review: {e}")
                        continue
                
                # Update upload status
                upload.processed_reviews = processed_count
                upload.status = 'completed' if processed_count > 0 else 'failed'
                db.session.commit()
                
                # Image already deleted for GDPR compliance
                
                if processed_count > 0:
                    flash(f'Framgångsrikt extraherade och analyserade {processed_count} textdelar från bilden!', 'success')
                    return redirect(url_for('dashboard', upload_id=upload.id))
                else:
                    flash('Ingen text kunde bearbetas från bilden.', 'error')
                    
            except Exception as e:
                # Ensure image is deleted even if processing fails
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    if filename:
                        logger.info(f"Cleaned up image file after error: {filename}")
                    else:
                        logger.info("Cleaned up image file after error")
                
                logger.error(f"Error processing image: {e}")
                if "text hittades" in str(e) or "tydligare" in str(e) or "meningsfulla" in str(e):
                    flash(str(e), 'error')
                else:
                    flash('Ett fel uppstod vid bearbetning av bilden. Kontrollera att bilden innehåller tydlig text och försök igen.', 'error')
                return redirect(request.url)
        
        else:
            # Handle file upload (existing logic)
            # Check if file was uploaded
            if 'file' not in request.files:
                flash('Ingen fil valdes.', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('Ingen fil valdes.', 'error')
                return redirect(request.url)
            
            if not file.filename or not allowed_file(file.filename):
                flash('Endast CSV-filer är tillåtna.', 'error')
                return redirect(request.url)
            
            try:
                # Save uploaded file
                if not file.filename:
                    flash('Ingen fil valdes.', 'error')
                    return redirect(request.url)
                filename = generate_unique_filename(file.filename)
                file_path = os.path.join('uploads', filename)
                file.save(file_path)
                
                # Parse reviews from file
                reviews_data = parse_csv_reviews(file_path)
                
                if not reviews_data:
                    flash('Inga giltiga recensioner hittades i filen.', 'error')
                    os.remove(file_path)
                    return redirect(request.url)
                
                # Check freemium limits
                if not check_freemium_limit(user_id, len(reviews_data), db):
                    flash(f'Freemium-gränsen (100 recensioner/månad) överskrids. Du försöker ladda upp {len(reviews_data)} recensioner.', 'error')
                    os.remove(file_path)
                    return redirect(url_for('pricing'))
                
                # Create upload record
                upload = ReviewUpload()
                upload.user_id = user_id
                upload.filename = file.filename
                upload.total_reviews = len(reviews_data)
                upload.status = 'processing'
                db.session.add(upload)
                db.session.commit()
                
                # Process reviews with sentiment analysis
                processed_count = 0
                for review_data in reviews_data:
                    try:
                        # Perform sentiment analysis
                        sentiment_result = sentiment_analyzer.analyze_sentiment(review_data['review_text'])
                        keywords = sentiment_analyzer.extract_keywords(review_data['review_text'])
                        
                        # Create review record
                        review = Review()
                        review.upload_id = upload.id
                        review.review_text = review_data['review_text']
                        review.rating = review_data.get('rating')
                        review.platform = review_data.get('platform', 'unknown')
                        review.reviewer_name = review_data.get('reviewer_name')
                        review.review_date = review_data.get('review_date')
                        review.sentiment = sentiment_result['sentiment']
                        review.sentiment_score = sentiment_result['score']
                        review.keywords = json.dumps(keywords, ensure_ascii=False)
                        db.session.add(review)
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing review: {e}")
                        continue
                
                # Update upload status
                upload.processed_reviews = processed_count
                upload.status = 'completed' if processed_count > 0 else 'failed'
                db.session.commit()
                
                # Clean up uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                if processed_count > 0:
                    flash(f'Framgångsrikt analyserade {processed_count} recensioner!', 'success')
                    return redirect(url_for('dashboard', upload_id=upload.id))
                else:
                    flash('Inga recensioner kunde bearbetas.', 'error')
                    
            except Exception as e:
                logger.error(f"Error in file upload: {e}")
                flash('Ett fel uppstod vid bearbetning av filen.', 'error')
    
    # Pass comprehensive onboarding state to template
    return render_template('upload.html', 
                         user=user, 
                         show_tutorial=show_tutorial,
                         show_onboarding_modal=show_onboarding_modal,
                         is_first_time=is_first_visit and onboarding_incomplete)

@app.route('/reports')
def reports():
    """Reports page"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Du måste logga in för att se rapporter.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('Användare hittades inte.', 'error')
        return redirect(url_for('login'))
    
    # Get user's reports
    reports = Report.query.filter_by(user_id=user_id).order_by(Report.generated_at.desc()).all()
    
    # Get user's uploads for report generation
    uploads = ReviewUpload.query.filter_by(user_id=user_id, status='completed').order_by(ReviewUpload.upload_date.desc()).all()
    
    return render_template('reports.html', user=user, reports=reports, uploads=uploads)

@app.route('/generate_report/<int:upload_id>')
def generate_report(upload_id):
    """Generate PDF report for an upload"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Du måste logga in.', 'error')
        return redirect(url_for('login'))
    
    # Check if upload belongs to user
    upload = ReviewUpload.query.filter_by(id=upload_id, user_id=user_id).first()
    if not upload:
        flash('Uppladdning hittades inte.', 'error')
        return redirect(url_for('reports'))
    
    user = User.query.get(user_id)
    
    try:
        # Get reviews data
        reviews = Review.query.filter_by(upload_id=upload_id).all()
        
        # Prepare data for report
        reviews_data = []
        for review in reviews:
            keywords = []
            if review.keywords:
                try:
                    keywords = json.loads(review.keywords)
                except:
                    keywords = []
            
            reviews_data.append({
                'review_text': review.review_text,
                'sentiment': review.sentiment,
                'sentiment_score': review.sentiment_score,
                'keywords': keywords,
                'rating': review.rating,
                'platform': review.platform,
                'reviewer_name': review.reviewer_name,
                'review_date': review.review_date
            })
        
        # Generate unique filename
        report_filename = f"rapport_{upload.filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        report_path = os.path.join('static', 'reports', report_filename)
        
        # Generate PDF report
        user_data = {
            'company_name': user.company_name if user else 'N/A',
            'email': user.email if user else 'N/A'
        }
        report_generator.generate_report(
            user_data=user_data,
            reviews_data=reviews_data,
            output_path=report_path
        )
        
        # Save report record
        report = Report()
        report.user_id = user_id
        report.upload_id = upload_id
        report.filename = report_filename
        report.file_path = report_path
        db.session.add(report)
        db.session.commit()
        
        # Send email notification for premium/enterprise users
        if EMAIL_ENABLED and user and user.plan in ['premium', 'enterprise']:
            try:
                report_data = {
                    'report_id': report.id,
                    'filename': report_filename,
                    'upload_filename': upload.filename,
                    'total_reviews': len(reviews_data),
                    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                
                user_data_for_email = {
                    'email': user.email,
                    'company_name': user.company_name if user.company_name else user.email,
                    'plan': user.plan
                }
                
                if send_report_notification(mail, user_data_for_email, report_data):
                    flash('Rapport genererad och e-post skickad!', 'success')
                else:
                    flash('Rapport genererad framgångsrikt! (E-post kunde inte skickas)', 'warning')
            except Exception as e:
                logger.error(f"Email notification failed: {e}")
                flash('Rapport genererad framgångsrikt! (E-post kunde inte skickas)', 'warning')
        else:
            flash('Rapport genererad framgångsrikt!', 'success')
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        flash('Ett fel uppstod vid generering av rapporten.', 'error')
    
    return redirect(url_for('reports'))

@app.route('/download_report/<int:report_id>')
def download_report(report_id):
    """Download a generated report"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Du måste logga in.', 'error')
        return redirect(url_for('login'))
    
    # Check if report belongs to user
    report = Report.query.filter_by(id=report_id, user_id=user_id).first()
    if not report or not os.path.exists(report.file_path):
        flash('Rapport hittades inte.', 'error')
        return redirect(url_for('reports'))
    
    return send_file(report.file_path, as_attachment=True, download_name=report.filename)

@app.route('/api/sentiment_data/<int:upload_id>')
def api_sentiment_data(upload_id):
    """API endpoint for sentiment data (for charts)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check if upload belongs to user
    upload = ReviewUpload.query.filter_by(id=upload_id, user_id=user_id).first()
    if not upload:
        return jsonify({'error': 'Upload not found'}), 404
    
    # Get sentiment distribution
    reviews = Review.query.filter_by(upload_id=upload_id).all()
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    for review in reviews:
        sentiment = review.sentiment or 'neutral'
        sentiment_counts[sentiment] += 1
    
    return jsonify(sentiment_counts)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Template filters
@app.template_filter('datetime')
def datetime_filter(value):
    if value:
        return value.strftime('%Y-%m-%d %H:%M')
    return ''

@app.template_filter('date')
def date_filter(value):
    if value:
        return value.strftime('%Y-%m-%d')
    return ''

# =============================================================================
# DEMO & ONBOARDING
# =============================================================================

@app.route('/demo')
def demo():
    """Interactive demo page for new users"""
    return render_template('demo.html')

@app.route('/api/demo_data')
def demo_data():
    """Return sample reviews for demo"""
    return jsonify(get_demo_reviews())

@app.route('/api/demo_csv')
def demo_csv():
    """Download sample CSV for demo"""
    from flask import make_response
    csv_content = get_demo_csv_content()
    response = make_response(csv_content)
    response.headers["Content-Disposition"] = "attachment; filename=exempel_recensioner.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

@app.route('/api/complete_onboarding', methods=['POST'])
def complete_onboarding():
    """Mark user's onboarding as completed"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    # Basic CSRF protection - check referer for same-origin
    referer = request.headers.get('Referer', '')
    if not referer.startswith(request.url_root):
        return jsonify({'success': False, 'error': 'Invalid request source'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'})
    
    # Mark onboarding as completed and first login as done
    user.onboarding_completed = True
    user.first_login = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Onboarding completed'})

# =============================================================================
# FOOTER PAGES - Company, Support & Legal
# =============================================================================

@app.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')

@app.route('/support')
def support():
    """Support/Help page"""
    return render_template('support.html')

@app.route('/about')
def about():
    """About Us page"""
    return render_template('about.html')

@app.route('/careers')
def careers():
    """Careers page"""
    return render_template('careers.html')

@app.route('/press')
def press():
    """Press page"""
    return render_template('press.html')

@app.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    """Terms of Service page"""
    return render_template('terms_of_service.html')

@app.route('/gdpr')
def gdpr():
    """GDPR page"""
    return render_template('gdpr.html')
