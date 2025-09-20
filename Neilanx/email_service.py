from flask_mail import Mail, Message
from flask import current_app, url_for
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def init_mail(app):
    """Initialize Flask-Mail with app configuration"""
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'benjamin.neilan16@gmail.com'
    app.config['MAIL_PASSWORD'] = os.environ.get('GMAIL_APP_PASSWORD', '')  # App password for Gmail
    app.config['MAIL_DEFAULT_SENDER'] = 'benjamin.neilan16@gmail.com'
    
    return Mail(app)

def send_report_notification(mail, user_data: Dict[str, Any], report_data: Dict[str, Any]) -> bool:
    """Send email notification when a report is generated for premium/enterprise users"""
    try:
        # Check if user has premium or enterprise plan
        if user_data.get('plan') not in ['premium', 'enterprise']:
            logger.info(f"User {user_data.get('email')} is not on premium/enterprise plan, skipping email")
            return False
            
        subject = f"📊 Din NeilanX-rapport är klar - {report_data['filename']}"
        
        # Generate download URL
        download_url = url_for('download_report', report_id=report_data['report_id'], _external=True)
        
        # Create HTML email content
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #2A77D4, #1e5aa8); color: white; padding: 30px; border-radius: 8px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">📊 Din rapport är klar!</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Från NeilanX AI-Recensionsanalys</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa; border-radius: 8px; margin-top: 20px;">
                <h2 style="color: #2A77D4; margin-top: 0;">Hej {user_data.get('company_name', user_data.get('email', 'kund'))}!</h2>
                
                <p>Din AI-rapport för <strong>{report_data['upload_filename']}</strong> är nu klar och redo för nedladdning.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #2A77D4; margin: 20px 0;">
                    <h3 style="color: #111827; margin-top: 0;">📈 Rapport-sammanfattning:</h3>
                    <ul style="color: #4B5563; line-height: 1.6;">
                        <li><strong>Antal recensioner:</strong> {report_data['total_reviews']}</li>
                        <li><strong>Sentimentanalys:</strong> Komplett AI-analys</li>
                        <li><strong>Nyckelord:</strong> Automatiskt extraherade</li>
                        <li><strong>Format:</strong> Professionell PDF-rapport</li>
                        <li><strong>Skapad:</strong> {report_data['generated_at']}</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{download_url}" 
                       style="background: #2A77D4; color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 8px; font-weight: bold; display: inline-block; box-shadow: 0 4px 12px rgba(42, 119, 212, 0.3);">
                        📥 Ladda ner din rapport
                    </a>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #111827; margin-top: 0;">💡 Tips för att använda rapporten:</h3>
                    <ul style="color: #4B5563; line-height: 1.6;">
                        <li>Använd sentimenttrenden för att förstå kundnöjdhet över tid</li>
                        <li>Fokusera på de vanligaste negativa nyckelorden för förbättringar</li>
                        <li>Dela positiva insikter med ditt team för motivation</li>
                        <li>Använd rapporten i presentationer och månadsrapporter</li>
                    </ul>
                </div>
                
                <p style="color: #6B7280; margin-top: 30px;">
                    Har du frågor om rapporten? Svara på detta email eller kontakta oss på 
                    <a href="mailto:benjamin.neilan16@gmail.com" style="color: #2A77D4;">benjamin.neilan16@gmail.com</a>
                </p>
                
                <p style="color: #6B7280; font-size: 14px; margin-top: 20px;">
                    Bästa hälsningar,<br>
                    <strong>NeilanX Team</strong><br>
                    <em>AI-driven recensionsanalys för svenska företag</em>
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #9CA3AF; font-size: 12px;">
                <p>© 2024 NeilanX. Malmö, Sverige</p>
                <p>Du får detta email eftersom du har Premium/Konsultpaket hos NeilanX.</p>
            </div>
        </body>
        </html>
        """
        
        # Create and send email
        msg = Message(
            subject=subject,
            recipients=[user_data['email']],
            html=html_body
        )
        
        mail.send(msg)
        logger.info(f"Report notification email sent successfully to {user_data['email']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send report notification email: {e}")
        return False

def send_weekly_report_summary(mail, user_data: Dict[str, Any], weekly_data: Dict[str, Any]) -> bool:
    """Send weekly summary email to premium/enterprise users (future feature)"""
    try:
        if user_data.get('plan') not in ['premium', 'enterprise']:
            return False
            
        subject = f"📈 Veckosammanfattning från NeilanX - Vecka {weekly_data.get('week_number')}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #2A77D4, #1e5aa8); color: white; padding: 30px; border-radius: 8px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">📈 Veckosammanfattning</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Dina recensionsinsikter från NeilanX</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa; border-radius: 8px; margin-top: 20px;">
                <h2 style="color: #2A77D4; margin-top: 0;">Vecka {weekly_data.get('week_number')} - Sammanfattning</h2>
                
                <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #10B981; margin: 20px 0;">
                    <h3 style="color: #111827; margin-top: 0;">📊 Nyckelstatistik:</h3>
                    <ul style="color: #4B5563; line-height: 1.6;">
                        <li><strong>Nya recensioner:</strong> {weekly_data.get('new_reviews', 0)}</li>
                        <li><strong>Genomsnittligt sentiment:</strong> {weekly_data.get('avg_sentiment', 'N/A')}</li>
                        <li><strong>Totalt antal rapporter:</strong> {weekly_data.get('total_reports', 0)}</li>
                    </ul>
                </div>
                
                <p style="color: #6B7280; margin-top: 30px;">
                    Logga in på din dashboard för att se detaljerad analys och generera nya rapporter.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_for('dashboard', _external=True)}" 
                       style="background: #2A77D4; color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 8px; font-weight: bold; display: inline-block;">
                        📊 Gå till Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=[user_data['email']],
            html=html_body
        )
        
        mail.send(msg)
        logger.info(f"Weekly summary email sent successfully to {user_data['email']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send weekly summary email: {e}")
        return False