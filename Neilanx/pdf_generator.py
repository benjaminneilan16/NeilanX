import os
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
import logging

logger = logging.getLogger(__name__)

class ReviewReportGenerator:
    def __init__(self):
        self.initialized = True
        # Swedish fonts and colors
        self.brand_colors = {
            'primary': '#2A77D4',
            'secondary': '#111827',
            'success': '#10B981',
            'warning': '#F59E0B',
            'danger': '#EF4444'
        }
    
    def _create_sentiment_chart(self, sentiment_counts: Dict[str, int], output_dir: str) -> str:
        """Create a pie chart for sentiment distribution"""
        try:
            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 6))
            
            labels = ['Positiva', 'Negativa', 'Neutrala']
            sizes = [sentiment_counts['positive'], sentiment_counts['negative'], sentiment_counts['neutral']]
            colors_list = ['#10B981', '#EF4444', '#F59E0B']
            
            # Only include non-zero values
            filtered_data = [(label, size, color) for label, size, color in zip(labels, sizes, colors_list) if size > 0]
            if filtered_data:
                labels, sizes, colors_list = zip(*filtered_data)
            
            pie_result = ax.pie(sizes, labels=labels, colors=colors_list, 
                                            autopct='%1.1f%%', startangle=90)
            if len(pie_result) == 3:
                wedges, texts, autotexts = pie_result
            else:
                wedges, texts = pie_result
                autotexts = []
            
            ax.set_title('Sentimentfördelning', fontsize=16, fontweight='bold', pad=20)
            
            # Make text larger and more readable
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')
            
            plt.tight_layout()
            
            # Save chart
            chart_path = os.path.join(output_dir, 'sentiment_chart.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            logger.error(f"Error creating sentiment chart: {e}")
            return ""
    
    def generate_report(self, user_data: Dict[str, Any], reviews_data: List[Dict[str, Any]], 
                       output_path: str) -> str:
        """Generate a professional PDF report"""
        
        try:
            # Calculate summary statistics
            sentiments = [review.get('sentiment', 'neutral') for review in reviews_data]
            sentiment_counts = {
                'positive': sentiments.count('positive'),
                'negative': sentiments.count('negative'),
                'neutral': sentiments.count('neutral')
            }
            
            total_reviews = len(reviews_data)
            
            if total_reviews == 0:
                return self._create_empty_report(output_path, user_data)
            
            # Create charts
            output_dir = os.path.dirname(output_path)
            chart_path = self._create_sentiment_chart(sentiment_counts, output_dir)
            
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor(self.brand_colors['primary']),
                alignment=1  # Center
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                textColor=colors.HexColor(self.brand_colors['secondary'])
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                textColor=colors.HexColor(self.brand_colors['secondary'])
            )
            
            # Title page
            story.append(Paragraph("NeilanX", title_style))
            story.append(Paragraph("AI-driven Recensionsanalys", heading_style))
            story.append(Spacer(1, 20))
            
            # Company info
            company_info = f"""
            <b>Företag:</b> {user_data.get('company_name', 'N/A')}<br/>
            <b>Rapportdatum:</b> {datetime.now().strftime('%Y-%m-%d')}<br/>
            <b>Antal analyserade recensioner:</b> {total_reviews}
            """
            story.append(Paragraph(company_info, body_style))
            story.append(Spacer(1, 30))
            
            # Summary statistics
            positive_pct = (sentiment_counts['positive'] / total_reviews) * 100
            negative_pct = (sentiment_counts['negative'] / total_reviews) * 100
            neutral_pct = (sentiment_counts['neutral'] / total_reviews) * 100
            
            story.append(Paragraph("SAMMANFATTNING", heading_style))
            
            # Summary table
            summary_data = [
                ['Sentiment', 'Antal', 'Procent'],
                ['Positiva recensioner', sentiment_counts['positive'], f'{positive_pct:.1f}%'],
                ['Negativa recensioner', sentiment_counts['negative'], f'{negative_pct:.1f}%'],
                ['Neutrala recensioner', sentiment_counts['neutral'], f'{neutral_pct:.1f}%']
            ]
            
            summary_table = Table(summary_data, colWidths=[6*cm, 3*cm, 3*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.brand_colors['primary'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Add chart if created successfully
            if chart_path and os.path.exists(chart_path):
                story.append(Image(chart_path, width=12*cm, height=9*cm))
                story.append(Spacer(1, 20))
            
            # Recommendations
            story.append(Paragraph("REKOMMENDATIONER", heading_style))
            
            recommendations = []
            if positive_pct > 70:
                recommendations.append("• Utmärkt! Majoriteten av era recensioner är positiva. Fortsätt med det goda arbetet.")
            elif positive_pct > 50:
                recommendations.append("• Bra resultat, men det finns utrymme för förbättring. Analysera negativa recensioner för förbättringsmöjligheter.")
            else:
                recommendations.append("• Fokusera på att förbättra kundupplevelsen baserat på negativ feedback.")
            
            if negative_pct > 30:
                recommendations.append("• Undersök vanliga klagomål och skapa handlingsplaner för att adressera dem.")
            
            recommendations.extend([
                "• Använd positiv feedback i marknadsföring och produktutveckling.",
                "• Följ upp regelbundet för att spåra förändringar över tid.",
                "• Överväg att implementera ett system för att svara på negativa recensioner."
            ])
            
            for rec in recommendations:
                story.append(Paragraph(rec, body_style))
            
            story.append(Spacer(1, 30))
            
            # Sample reviews
            story.append(Paragraph("EXEMPEL PÅ RECENSIONER", heading_style))
            
            for sentiment, sentiment_swedish in [('positive', 'POSITIVA'), ('negative', 'NEGATIVA'), ('neutral', 'NEUTRALA')]:
                sentiment_reviews = [r for r in reviews_data if r.get('sentiment') == sentiment]
                if sentiment_reviews:
                    story.append(Paragraph(f"{sentiment_swedish} RECENSIONER:", 
                                         ParagraphStyle('SentimentHeader', parent=body_style, fontSize=12, fontName='Helvetica-Bold')))
                    
                    for i, review in enumerate(sentiment_reviews[:2]):  # Show max 2 per sentiment
                        review_text = review.get('review_text', '')
                        if len(review_text) > 200:
                            review_text = review_text[:200] + "..."
                        
                        story.append(Paragraph(f"• {review_text}", body_style))
                    
                    story.append(Spacer(1, 15))
            
            # Footer
            story.append(Spacer(1, 30))
            footer_text = """
            <br/><br/>
            <i>Denna rapport genererades av NeilanX - AI-driven recensionsanalys för svenska e-handlare.</i><br/>
            <i>© 2024 NeilanX. Alla rättigheter förbehållna.</i>
            """
            story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=body_style, fontSize=9, textColor=colors.grey)))
            
            # Build PDF
            doc.build(story)
            
            # Clean up chart file
            if chart_path and os.path.exists(chart_path):
                try:
                    os.remove(chart_path)
                except:
                    pass
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return self._create_empty_report(output_path, user_data)
    
    def _create_empty_report(self, output_path: str, user_data: Dict[str, Any]) -> str:
        """Create a minimal report when there's an error"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            story.append(Paragraph("NeilanX - Recensionsanalys", styles['Title']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Företag: {user_data.get('company_name', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Datum: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            story.append(Spacer(1, 20))
            story.append(Paragraph("Rapporten kunde inte genereras på grund av ett tekniskt fel. Kontakta support för hjälp.", styles['Normal']))
            
            doc.build(story)
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating empty report: {e}")
            # Fallback to text file
            with open(output_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                f.write("Rapport kunde inte genereras på grund av ett fel.\n")
            return output_path.replace('.pdf', '.txt')

# Global instance
report_generator = ReviewReportGenerator()