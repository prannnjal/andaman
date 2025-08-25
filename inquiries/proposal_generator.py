import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
from django.utils import timezone
import uuid

class ProposalGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for the proposal"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6366f1')
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#4f46e5')
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            leading=16
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#374151')
        )
    
    def generate_proposal_pdf(self, inquiry, custom_message="", company_info=None):
        """Generate a professional PDF proposal for the given inquiry"""
        
        # Create unique filename
        filename = f"proposal_{inquiry.student_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, 'proposals', filename)
        
        # Ensure proposals directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        # Build PDF content
        story = []
        
        # Add company header
        story.extend(self.create_company_header(company_info))
        
        # Add proposal title
        story.append(Paragraph(f"Educational Proposal for {inquiry.student_name}", self.title_style))
        story.append(Spacer(1, 20))
        
        # Add proposal details
        story.extend(self.create_proposal_details(inquiry))
        
        # Add custom message if provided
        if custom_message:
            story.extend(self.create_custom_message_section(custom_message))
        
        # Add services section
        story.extend(self.create_services_section())
        
        # Add pricing section
        story.extend(self.create_pricing_section(inquiry))
        
        # Add terms and conditions
        story.extend(self.create_terms_section())
        
        # Add contact information
        story.extend(self.create_contact_section(company_info))
        
        # Build PDF
        doc.build(story)
        
        return filepath, filename
    
    def create_company_header(self, company_info):
        """Create company header section"""
        story = []
        
        # Company name and logo placeholder
        company_name = company_info.get('name', 'Your Educational Institution') if company_info else 'Your Educational Institution'
        company_address = company_info.get('address', 'Your Address') if company_info else 'Your Address'
        company_phone = company_info.get('phone', '+91-XXXXXXXXXX') if company_info else '+91-XXXXXXXXXX'
        company_email = company_info.get('email', 'info@yourinstitution.com') if company_info else 'info@yourinstitution.com'
        
        # Company header table
        header_data = [
            [Paragraph(company_name, self.subtitle_style), 
             Paragraph(f"Date: {timezone.now().strftime('%B %d, %Y')}", self.normal_style)],
            [Paragraph(company_address, self.normal_style), 
             Paragraph(f"Proposal #: {timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}", self.normal_style)],
            [Paragraph(f"Phone: {company_phone}", self.normal_style), ""],
            [Paragraph(f"Email: {company_email}", self.normal_style), ""]
        ]
        
        header_table = Table(header_data, colWidths=[4*inch, 2*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def create_proposal_details(self, inquiry):
        """Create proposal details section"""
        story = []
        
        story.append(Paragraph("Proposal Details", self.subtitle_style))
        story.append(Spacer(1, 15))
        
        # Student and parent information
        details_data = [
            ['Student Information', ''],
            ['Student Name:', inquiry.student_name],
            ['Class:', inquiry.student_class],
            ['Parent Name:', inquiry.parent_name],
            ['Contact Number:', inquiry.mobile_number or 'Not provided'],
            ['Email Address:', inquiry.email or 'Not provided'],
            ['Address:', inquiry.address or 'Not provided'],
            ['Inquiry Source:', inquiry.inquiry_source],
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f3f4f6')),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f9fafb')),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def create_custom_message_section(self, custom_message):
        """Create custom message section"""
        story = []
        
        story.append(Paragraph("Personal Message", self.subtitle_style))
        story.append(Spacer(1, 10))
        
        message_style = ParagraphStyle(
            'CustomMessage',
            parent=self.normal_style,
            leftIndent=20,
            rightIndent=20,
            backColor=colors.HexColor('#fef3c7'),
            borderPadding=10,
            borderWidth=1,
            borderColor=colors.HexColor('#f59e0b')
        )
        
        story.append(Paragraph(custom_message, message_style))
        story.append(Spacer(1, 20))
        
        return story
    
    def create_services_section(self):
        """Create services section"""
        story = []
        
        story.append(Paragraph("Our Educational Services", self.subtitle_style))
        story.append(Spacer(1, 15))
        
        services_data = [
            ['Service', 'Description', 'Benefits'],
            ['Academic Excellence', 'Comprehensive curriculum designed for holistic development', 'Strong foundation for future success'],
            ['Experienced Faculty', 'Qualified and experienced teachers', 'Quality education and mentorship'],
            ['Modern Infrastructure', 'State-of-the-art facilities and technology', 'Enhanced learning experience'],
            ['Individual Attention', 'Personalized attention to each student', 'Better understanding and growth'],
            ['Extracurricular Activities', 'Sports, arts, and cultural programs', 'Overall personality development'],
            ['Career Guidance', 'Professional career counseling and guidance', 'Clear career path and goals'],
        ]
        
        services_table = Table(services_data, colWidths=[1.5*inch, 2.5*inch, 2*inch])
        services_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ]))
        
        story.append(services_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def create_pricing_section(self, inquiry):
        """Create pricing section"""
        story = []
        
        story.append(Paragraph("Investment Details", self.subtitle_style))
        story.append(Spacer(1, 15))
        
        # Calculate fees based on class (you can customize this)
        base_fee = self.get_base_fee_for_class(inquiry.student_class)
        
        pricing_data = [
            ['Fee Component', 'Amount (₹)', 'Description'],
            ['Tuition Fee', f'₹{base_fee:,}', 'Monthly tuition fee'],
            ['Admission Fee', '₹5,000', 'One-time admission fee'],
            ['Development Fee', '₹2,000', 'Annual development fee'],
            ['Transportation', '₹1,500', 'Monthly transportation (optional)'],
            ['', '', ''],
            ['Total Monthly', f'₹{base_fee + 1500:,}', 'Including transportation'],
            ['Total Annual', f'₹{(base_fee + 1500) * 12 + 7000:,}', 'Including all fees'],
        ]
        
        pricing_table = Table(pricing_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        pricing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 6), (-1, 7), colors.HexColor('#fef3c7')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 6), (-1, 7), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ]))
        
        story.append(pricing_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def get_base_fee_for_class(self, student_class):
        """Get base fee for different classes"""
        fee_structure = {
            'Play School': 3000,
            'Nursery': 3500,
            'LKG': 4000,
            'UKG': 4500,
            'Grade 1': 5000,
            'Grade 2': 5500,
            'Grade 3': 6000,
            'Grade 4': 6500,
            'Grade 5': 7000,
            'Grade 6': 7500,
            'Grade 7': 8000,
            'Grade 8': 8500,
            'Grade 9': 9000,
            'Grade 10': 9500,
            'Grade 11': 10000,
            'Grade 12': 10500,
        }
        return fee_structure.get(student_class, 5000)
    
    def create_terms_section(self):
        """Create terms and conditions section"""
        story = []
        
        story.append(Paragraph("Terms & Conditions", self.subtitle_style))
        story.append(Spacer(1, 15))
        
        terms = [
            "• Fees are payable monthly in advance by the 5th of each month",
            "• Late payment may incur additional charges",
            "• 30 days notice is required for withdrawal",
            "• The institution reserves the right to modify fee structure with prior notice",
            "• All disputes are subject to local jurisdiction",
            "• This proposal is valid for 30 days from the date of issue"
        ]
        
        for term in terms:
            story.append(Paragraph(term, self.normal_style))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def create_contact_section(self, company_info):
        """Create contact information section"""
        story = []
        
        story.append(Paragraph("Contact Information", self.subtitle_style))
        story.append(Spacer(1, 15))
        
        company_name = company_info.get('name', 'Your Educational Institution') if company_info else 'Your Educational Institution'
        company_address = company_info.get('address', 'Your Address') if company_info else 'Your Address'
        company_phone = company_info.get('phone', '+91-XXXXXXXXXX') if company_info else '+91-XXXXXXXXXX'
        company_email = company_info.get('email', 'info@yourinstitution.com') if company_info else 'info@yourinstitution.com'
        
        contact_data = [
            ['Institution:', company_name],
            ['Address:', company_address],
            ['Phone:', company_phone],
            ['Email:', company_email],
            ['Website:', company_info.get('website', 'www.yourinstitution.com') if company_info else 'www.yourinstitution.com'],
        ]
        
        contact_table = Table(contact_data, colWidths=[1.5*inch, 4.5*inch])
        contact_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ]))
        
        story.append(contact_table)
        story.append(Spacer(1, 30))
        
        # Add footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.normal_style,
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6b7280')
        )
        
        story.append(Paragraph("Thank you for considering our educational services. We look forward to partnering in your child's educational journey.", footer_style))
        
        return story

