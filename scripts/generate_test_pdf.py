from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)

text = """SOFTWARE LICENSE AGREEMENT

This Software License Agreement (the "Agreement") is entered into as of July 15, 2026, by and between NexSoft Inc., a Delaware corporation with its principal place of business at 100 Tech Park Drive, San Francisco, CA 94105 ("Licensor"), and Global Corp Ltd., a UK limited company with registered address at 1 London Bridge, London SE1 9GF ("Licensee").

1. DEFINITIONS
1.1 "Software" means the NexSoft Enterprise Suite version 4.2, including all updates and modifications.
1.2 "Documentation" means the user manuals and technical documentation provided with the Software.
1.3 "Authorized Users" means employees of Licensee who are authorized to use the Software.

2. LICENSE GRANT
Licensor grants Licensee a non-exclusive, non-transferable, worldwide license to use the Software for a period of three (3) years commencing on the Effective Date. The license is limited to 500 Authorized Users.

3. FEES AND PAYMENT
Licensee shall pay Licensor an annual license fee of $150,000 USD, payable in quarterly installments of $37,500 USD. Payments are due within 30 days of invoice date. Late payments shall accrue interest at 1.5% per month.

4. CONFIDENTIALITY
Each party agrees to maintain the confidentiality of the other party's Confidential Information for a period of five (5) years from the date of disclosure.

5. INTELLECTUAL PROPERTY
All rights, title, and interest in and to the Software and Documentation shall remain solely with Licensor. Licensee shall not reverse engineer, decompile, or disassemble the Software.

6. WARRANTY AND DISCLAIMER
Licensor warrants that the Software will perform substantially in accordance with the Documentation for 90 days from delivery. EXCEPT AS PROVIDED HEREIN, THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.

7. LIMITATION OF LIABILITY
Neither party shall be liable for any indirect, incidental, or consequential damages. Licensor's total liability shall not exceed the license fees paid by Licensee in the 12 months preceding the claim.

8. TERMINATION
Either party may terminate this Agreement upon 30 days written notice if the other party materially breaches any provision and fails to cure within 30 days.

9. GOVERNING LAW
This Agreement shall be governed by the laws of the State of New York, without regard to conflict of laws principles.

10. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement between the parties regarding the subject matter hereof.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first above written.

NexSoft Inc.                        Global Corp Ltd.

________________________           ________________________
By: Jane Smith                      By: John Doe
Title: CEO                          Title: VP Engineering
Date: July 15, 2026                 Date: July 15, 2026
"""

pdf.multi_cell(0, 5, text)
pdf.output("C:\\LLM\\nexus-clm\\test_contract.pdf")
print("PDF generated: test_contract.pdf")
