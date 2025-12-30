from fpdf import FPDF
from datetime import date
from decimal import Decimal
from typing import List, Dict
from sqlmodel import Session, select
from app.models.domain import Operation, Allocation, Owner, Category, Lot, OperationType
from app.utils.formatters import format_currency
import os

class AnnualReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Load DejaVuSans for full Unicode support (€, accents, etc.)
        font_dir = "/usr/share/fonts/truetype/dejavu"
        regular = os.path.join(font_dir, "DejaVuSans.ttf")
        bold = os.path.join(font_dir, "DejaVuSans-Bold.ttf")
        
        self.font_family_main = "helvetica" # Fallback
        
        if os.path.exists(regular):
            self.add_font("DejaVu", "", regular, uni=True)
            self.font_family_main = "DejaVu"
            
        if os.path.exists(bold):
            self.add_font("DejaVu", "B", bold, uni=True)
            
        self.set_auto_page_break(auto=True, margin=20)
    
    def header(self):
        if self.page_no() == 1:
            # Stylish Top Bar
            self.set_fill_color(63, 81, 181) # Indigo 600
            self.rect(0, 0, 210, 40, "F")
            
            self.set_xy(10, 10)
            self.set_font(self.font_family_main, "B", 24)
            self.set_text_color(255, 255, 255)
            self.cell(0, 15, "VIGIE", ln=True, align="L")
            
            self.set_font(self.font_family_main, "", 12)
            self.set_text_color(224, 231, 255) # Indigo 100
            self.cell(0, 5, "Gestion Immobilière & Indivision", ln=True, align="L")
            self.ln(20)

    def footer(self):
        self.set_y(-15)
        # Avoid "I" style as it might not be loaded
        self.set_font(self.font_family_main, "", 8)
        self.set_text_color(148, 163, 184) # Slate 400
        self.cell(0, 10, f"Généré le {date.today().strftime('%d/%m/%Y')} - Page {self.page_no()}/{{nb}}", align="C")

def generate_owner_annual_report(session: Session, owner_id: int, year: int) -> bytes:
    owner = session.get(Owner, owner_id)
    if not owner:
        return b""

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    statement = (
        select(Allocation)
        .join(Operation)
        .where(Allocation.owner_id == owner_id)
        .where(Operation.date >= start_date)
        .where(Operation.date <= end_date)
        .order_by(Operation.date)
    )
    allocations = session.exec(statement).unique().all()

    # Calculate totals
    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")
    
    details = []
    for alloc in allocations:
        op = alloc.operation
        if not op: continue
        
        is_income = op.type == OperationType.ENTREE
        amount = alloc.amount
        if is_income:
            total_income += amount
        else:
            total_expense += amount

        details.append({
            "date": op.date.strftime("%d/%m/%Y"),
            "label": op.label,
            "category": op.category_ref.name if op.category_ref else "-",
            "lot": op.lot.name if op.lot else "-",
            "amount": amount,
            "is_income": is_income
        })

    if not details:
        return b""

    # Create PDF
    pdf = AnnualReportPDF()
    pdf.add_page()
    
    # --- Titre du Rapport ---
    pdf.set_font(pdf.font_family_main, "B", 18)
    pdf.set_text_color(30, 41, 59) # Slate 800
    pdf.cell(0, 15, f"Rapport Annuel {year}", ln=True)
    
    # --- Infos Propriétaire ---
    pdf.set_font(pdf.font_family_main, "B", 12)
    pdf.set_text_color(71, 85, 105) # Slate 600
    pdf.cell(35, 8, "Propriétaire :")
    pdf.set_font(pdf.font_family_main, "", 12)
    pdf.set_text_color(15, 23, 42) # Slate 900
    pdf.cell(0, 8, owner.name, ln=True)
    
    pdf.set_font(pdf.font_family_main, "B", 12)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(35, 8, "Période :")
    pdf.set_font(pdf.font_family_main, "", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, f"01/01/{year} au 31/12/{year}", ln=True)
    pdf.ln(10)

    # --- Bloc Résumé (Premium) ---
    net_balance = total_income - total_expense
    
    # Background - bloc plus compact (30mm au lieu de 40mm)
    curr_y = pdf.get_y()
    pdf.set_fill_color(248, 250, 252) # Slate 50
    pdf.rect(10, curr_y, 190, 28, "F")
    pdf.set_draw_color(226, 232, 240) # Slate 200
    pdf.rect(10, curr_y, 190, 28, "D")
    
    pdf.set_xy(15, curr_y + 3)
    pdf.set_font(pdf.font_family_main, "B", 10)
    pdf.set_text_color(100, 116, 139) # Slate 500
    pdf.cell(60, 6, "TOTAL REVENUS")
    pdf.cell(60, 6, "TOTAL DÉPENSES")
    pdf.cell(60, 6, "SOLDE NET", ln=True)
    
    pdf.set_x(15)
    pdf.set_font(pdf.font_family_main, "B", 16)
    pdf.set_text_color(16, 185, 129) # Emerald 500
    pdf.cell(60, 10, format_currency(total_income))
    
    pdf.set_text_color(244, 63, 94) # Rose 500
    pdf.cell(60, 10, format_currency(total_expense))
    
    color = (5, 150, 105) if net_balance >= 0 else (225, 29, 72)
    pdf.set_text_color(*color)
    pdf.cell(60, 10, format_currency(net_balance, show_sign=True), ln=True)
    
    pdf.set_y(curr_y + 32)  # Espacement réduit après le bloc

    # --- Tableau des Opérations ---
    pdf.set_font(pdf.font_family_main, "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "Détail des Opérations", ln=True)
    
    # En-tête Tableau (police réduite pour plus d'espace)
    pdf.set_fill_color(241, 245, 249) # Slate 100
    pdf.set_draw_color(203, 213, 225) # Slate 300
    pdf.set_text_color(71, 85, 105) # Slate 600
    pdf.set_font(pdf.font_family_main, "B", 8)
    
    # Colonnes ajustées: DATE 22, LIBELLÉ 90, CATÉGORIE 30, MONTANT 48 = 190
    pdf.cell(22, 8, "DATE", border=1, align="C", fill=True)
    pdf.cell(90, 8, "LIBELLÉ / LOT", border=1, align="L", fill=True)
    pdf.cell(30, 8, "CATÉGORIE", border=1, align="C", fill=True)
    pdf.cell(48, 8, "MONTANT PART", border=1, align="R", fill=True)
    pdf.ln()

    # Lignes du tableau (police réduite pour afficher plus de texte)
    pdf.set_font(pdf.font_family_main, "", 7)
    pdf.set_text_color(15, 23, 42)
    
    for i, d in enumerate(details):
        if pdf.get_y() > 275:
            pdf.add_page()
            # On ne remet pas l'en-tête ici pour l'instant pour gagner de la place, 
            # mais fpdf le gérerait avec une méthode dédiée si besoin.
            
        fill = (i % 2 == 1)
        pdf.set_fill_color(252, 253, 254) # Presque blanc pour alternance
        
        pdf.cell(22, 7, d["date"], border="B", align="C", fill=fill)
        
        # Concat libellé et lot - plus de caractères possibles avec police réduite
        txt = f"{d['label']} ({d['lot']})"
        if len(txt) > 70: txt = txt[:67] + "..."
        pdf.cell(90, 7, txt, border="B", fill=fill)
        
        cat = d["category"][:18]
        pdf.cell(30, 7, cat, border="B", align="C", fill=fill)
        
        if d["is_income"]:
            pdf.set_text_color(5, 150, 105)
            val = f"+ {format_currency(d['amount'])}"
        else:
            pdf.set_text_color(225, 29, 72)
            val = f"- {format_currency(d['amount'])}"
            
        pdf.cell(48, 7, val, border="B", align="R", fill=fill)
        pdf.set_text_color(15, 23, 42)
        pdf.ln()

    # Convertir en bytes proprement pour NiceGUI
    output_bytes = pdf.output()
    return bytes(output_bytes)
