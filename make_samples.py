"""Demo ke liye nakli (fake) documents banata hai -> samples/ folder."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import date, timedelta
f=lambda n:(date.today()+timedelta(days=n)).strftime('%d %B %Y')
import docx

out = Path(__file__).parent / "samples"; out.mkdir(exist_ok=True)

def pdf(name, pages):
    c = canvas.Canvas(str(out / name), pagesize=A4)
    for text in pages:
        y = 800
        for line in text.split("\n"):
            c.drawString(50, y, line); y -= 18
        c.showPage()
    c.save()

pdf("Sharma_Leather_Supply_Contract_2025.pdf", [
 "SUPPLY AGREEMENT\nThis agreement is made on 12 April 2025 between Kanpur Footwear Pvt Ltd (Buyer)\nand Sharma Leather Traders (Seller).\n1. The Seller shall supply 5,000 sq ft of finished buffalo leather every month.\n2. Rate: Rs 185 per sq ft, GST extra as applicable.",
 "3. Payment terms: 45 days from invoice date. Late payment attracts interest at 18% per annum.\n4. Penalty: delay in delivery beyond 7 days will attract 2% deduction per week.\n5. Term: this contract is valid for 12 months and renews only by written consent.\n6. Jurisdiction: courts at Kanpur Nagar only.\nContract expiry date: "+f(12)+" - renewal notice due 15 days before."])
pdf("Verma_Textiles_Contract_2024.pdf", [
 "SALES CONTRACT\nBetween Kanpur Footwear Pvt Ltd and Verma Textiles dated 03 June 2024.\nVerma Textiles will supply lining cloth 20,000 metres at Rs 42 per metre.\nPayment within 30 days. Advance of Rs 2,00,000 paid at signing.\nArbitration in Lucknow."])
pdf("GST_Notice_Gupta_Traders.pdf", [
 "GST DEPARTMENT NOTICE\nTo: Gupta Traders, Kanpur. GSTIN 09ABCDE1234F1Z5\nSubject: Mismatch between GSTR-1 and GSTR-3B for FY 2023-24.\nTax difference Rs 1,84,500. Last date to file reply: "+f(-3)+" (extension may be sought)."])
pdf("Rent_Agreement_Civil_Lines_Shop.pdf", [
 "RENT AGREEMENT\nLandlord: Mr. Anil Mishra. Tenant: Rajesh Kumar. Shop No. 14, Civil Lines, Kanpur.\nMonthly rent Rs 28,000. Security deposit Rs 1,68,000. Rent increases 10% every 11 months.\nLock-in period: 6 months.\nThis agreement is valid until "+f(47)+"."])

d = docx.Document()
d.add_heading("Legal Opinion - Property Dispute, Arya Nagar", 1)
d.add_paragraph("Client: Mrs. Sunita Dubey. The sale deed dated 5 March 2019 shows plot area 200 sq yards. "
                "The opposing party claims 220 sq yards. We recommend filing a suit for declaration "
                "in the Civil Court, Kanpur Nagar, along with a demand for local survey (naksha).")
d.add_paragraph("मकान का बैनामा 5 मार्च 2019 को हुआ था। विपक्षी पक्ष ने सीमा विवाद उठाया है।")
d.save(out / "Legal_Opinion_Dubey.docx")

(out / "Machine_Maintenance_Log.txt").write_text(
 "Plant: Unit 2 Jajmau. Press machine PM-07 breakdown on 14 Feb 2025. Hydraulic seal replaced.\n"
  "Cost Rs 12,400. Vendor: Singh Hydraulics. Next service due "+f(25)+".", encoding="utf-8")
print("Samples ban gaye:", out)
