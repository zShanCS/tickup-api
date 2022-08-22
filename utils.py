from square.client import Client
import uuid
from PIL import Image as PIL_Image
from borb.pdf import Document
from borb.pdf.page.page import Page

from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from decimal import Decimal
from borb.pdf.canvas.layout.image.image import Image
import os
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable as Table
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.layout_element import Alignment
from datetime import datetime
import random
from borb.pdf.canvas.color.color import HexColor, X11Color

from borb.pdf.canvas.layout.table.table import TableCell

from borb.pdf.pdf import PDF



def make_idemp_key():
    return str(uuid.uuid4())


def create_checkout_link(access_token, location_id, ticket_name, quantity, unit_price, redirect_url,currency='USD'):
    print(currency, redirect_url)
    if not currency:
        currency = "USD"
    client = Client(
        access_token=access_token,
        environment='sandbox')
    result = client.checkout.create_checkout(
    location_id = location_id,
    body = {
        "idempotency_key": make_idemp_key(),
        "order": {
        "order": {
            "location_id": location_id,
            "line_items": [
            {
                "name": ticket_name,
                "quantity": quantity,
                "base_price_money": {
                "amount": unit_price,
                "currency": currency
                }
            }
            ]
        },
        "idempotency_key": make_idemp_key()
        },
        "redirect_url": redirect_url
    }
    )
    return result


def obtain_oauth(access_token,own_client_id, own_secret, code, grant_type="authorization_code"):
    client = Client(
        access_token=access_token,
        environment='sandbox')


    result = client.o_auth.obtain_token(
        body = {
            "client_id": own_client_id,
            "client_secret": own_secret,
            "code": code,
            "grant_type": grant_type
        }
    )

    if result.is_success():
        print(result.body)
        return result
    elif result.is_error():
        return result
        print(result.errors)


def create_reciept(item, seller, checkout):
    # Create document
    pdf = Document()

    # Add page
    page = Page()
    pdf.add_page(page)

    page_layout = SingleColumnLayout(page)
    page_layout.vertical_margin = page.get_page_info().get_height() * Decimal(0.02)

    
    table_seller = Table(number_of_rows=3, number_of_columns=1, horizontal_alignment=Alignment.CENTERED)
	
    table_seller.add(Paragraph(f"{seller.name}", horizontal_alignment=Alignment.CENTERED, ))
    table_seller.add(Paragraph(f"Thank You for buying Ticket with us.", font_color= HexColor('808080'), horizontal_alignment=Alignment.CENTERED))
    table_seller.add(Paragraph('Show this ticket on your on boarding.', font_color= HexColor('808080'), horizontal_alignment=Alignment.CENTERED))
    
    table_seller.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))    		
    table_seller.no_borders()

    page_layout.add(table_seller) 
    
    page_layout.add(_build_invoice_information(checkout=checkout, item=item))

    try:
        img = PIL_Image.open(f'{item.image}')

        basewidth = 300
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), PIL_Image.LANCZOS)
        
        page_layout.add(    
            Image(        
            img,        
            width=Decimal(basewidth),        
            height=Decimal(hsize),    
            ))
    except Exception as e:
        print('error on opeeing pic',e)
        pass

    table_001 = Table(number_of_rows=3, number_of_columns=1)
	
    table_001.add(Paragraph(f"{item.title}"))
    table_001.add(Paragraph(f"{item.description}"))
    table_001.add(Paragraph(' '))
    
    table_001.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))    		
    table_001.no_borders()

    page_layout.add(table_001)    


    page_layout.add(Paragraph(" "))

    # page_layout.add(_build_billing_and_shipping_information())

    
    # Itemized description
    page_layout.add(_build_itemized_description_table(item=item, checkout=checkout))

    path = f"receipts"
    filename = f'{checkout.checkout_id}.pdf'
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename), "wb") as pdf_file_handle:
        PDF.dumps(pdf_file_handle, pdf)
    
    
    return f'receipts/{checkout.checkout_id}.pdf'







def _build_invoice_information(checkout, item):    
    table_001 = Table(number_of_rows=4, number_of_columns=2)
	
    # table_001.add(Paragraph(" "))    
    # table_001.add(Paragraph(" "))    
    table_001.add(Paragraph("Invoice Date :", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT))    
    now = datetime.now()    
    table_001.add(Paragraph("%d/%d/%d" % (now.day, now.month, now.year)))
	
    # table_001.add(Paragraph(" "))    
    # table_001.add(Paragraph(" "))    
    table_001.add(Paragraph("Invoice #", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT))
    table_001.add(Paragraph(f"{checkout.checkout_id}"))  


    # table_001.add(Paragraph(" "))    
    table_001.add(Paragraph("Departure :", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT))
    table_001.add(Paragraph(f"{item.departure_date}"))   
	
    # table_001.add(Paragraph(" "))    
    # table_001.add(Paragraph(" "))    
    # table_001.add(Paragraph("Due Date", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT))
    # table_001.add(Paragraph("%d/%d/%d" % (now.day, now.month, now.year))) 
	
    # table_001.add(Paragraph("[Email Address]"))    
    # table_001.add(Paragraph(" "))
    # table_001.add(Paragraph(" "))

    # table_001.add(Paragraph(" "))
    # table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))    		
    table_001.no_borders()
    return table_001



def _build_billing_and_shipping_information():  
    table_001 = Table(number_of_rows=6, number_of_columns=1)  
    table_001.add(  
        Paragraph(  
            "BILL TO",  
            background_color=HexColor("263238"),  
            font_color=X11Color("White"),  
        )  
    )  
    # table_001.add(  
    #     Paragraph(  
    #         "SHIP TO",  
    #         background_color=HexColor("263238"),  
    #         font_color=X11Color("White"),  
    #     )  
    # )  
    table_001.add(Paragraph("[Recipient Name]"))        # BILLING  
    # table_001.add(Paragraph("[Recipient Name]"))        # SHIPPING  
    table_001.add(Paragraph("[Company Name]"))          # BILLING  
    # table_001.add(Paragraph("[Company Name]"))          # SHIPPING  
    table_001.add(Paragraph("[Street Address]"))        # BILLING  
    # table_001.add(Paragraph("[Street Address]"))        # SHIPPING  
    table_001.add(Paragraph("[City, State, ZIP Code]")) # BILLING  
    # table_001.add(Paragraph("[City, State, ZIP Code]")) # SHIPPING  
    table_001.add(Paragraph("[Phone]"))                 # BILLING  
    # table_001.add(Paragraph("[Phone]"))                 # SHIPPING  
    table_001.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))  
    table_001.no_borders()  
    return table_001


def _build_itemized_description_table(item, checkout):  
    table_001 = Table(number_of_rows=3, number_of_columns=4)  
    for h in ["DESCRIPTION", "QTY", "UNIT PRICE", "AMOUNT"]:  
        table_001.add(  
            TableCell(  
                Paragraph(h, font_color=X11Color("White")),  
                background_color=HexColor("016934"),  
            )  
        )  
  
    odd_color = HexColor("BBBBBB")  
    even_color = HexColor("FFFFFF")  
    for row_number, print_item in enumerate([(item.title, checkout.quantity, item.price/100)]):  
        c = even_color if row_number % 2 == 0 else odd_color  
        table_001.add(TableCell(Paragraph(print_item[0]), background_color=c))  
        table_001.add(TableCell(Paragraph(str(print_item[1])), background_color=c))  
        table_001.add(TableCell(Paragraph("$ " + str(print_item[2])), background_color=c))  
        table_001.add(TableCell(Paragraph("$ " + str(print_item[1] * print_item[2])), background_color=c))  
	  
	# # Optionally add some empty rows to have a fixed number of rows for styling purposes
    # for row_number in range(3, 10):  
    #     c = even_color if row_number % 2 == 0 else odd_color  
    #     for _ in range(0, 4):  
    #         table_001.add(TableCell(Paragraph(" "), background_color=c))  
  
    # table_001.add(TableCell(Paragraph("Subtotal", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT,), col_span=3,))  
    # table_001.add(TableCell(Paragraph("$ 1,180.00", horizontal_alignment=Alignment.RIGHT)))  
    # table_001.add(TableCell(Paragraph("Discounts", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT,),col_span=3,))  
    # table_001.add(TableCell(Paragraph("$ 177.00", horizontal_alignment=Alignment.RIGHT)))  
    # table_001.add(TableCell(Paragraph("Taxes", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT), col_span=3,))  
    # table_001.add(TableCell(Paragraph("$ 100.30", horizontal_alignment=Alignment.RIGHT)))  
    table_001.add(TableCell(Paragraph("Total", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT  ), col_span=3,))  
    table_001.add(TableCell(Paragraph(f"{checkout.checkout_total/100}", horizontal_alignment=Alignment.RIGHT)))  
    table_001.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))  
    table_001.no_borders()  
    return table_001