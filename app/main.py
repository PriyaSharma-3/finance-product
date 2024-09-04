from fastapi import FastAPI, Depends, UploadFile, File, Form, status, HTTPException, Query
from typing import List
import pandas as pd
from dotenv import load_dotenv
import re
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse,HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Login, Finance, Expenses, Calculation, Invoice
from datetime import datetime
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from io import BytesIO
import json
from difflib import get_close_matches

app = FastAPI()

# Load environment variables
load_dotenv()

class ExpenseCategory(BaseModel):
    expense: str

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, 'output': "Hello World", 'main_request': ""}
    )
    
@app.get("/login/", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logout/", response_class=HTMLResponse)
async def get_logout(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/search/", response_class=HTMLResponse)
async def search(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})


@app.get("/upload_excel/", response_class=HTMLResponse)
async def upload_excel(request: Request):
    return templates.TemplateResponse("upload_excel.html", {"request": request})

@app.get("/add_expenses/", response_class=HTMLResponse)
async def add_expenses(request: Request):
    return templates.TemplateResponse("add_expenses.html", {"request": request})

@app.post("/login/", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(Login).filter(Login.username == username, Login.password == password).first()
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        error_message = "Incorrect username or password"
        return templates.TemplateResponse("index.html", {"request": request, "error": error_message}, status_code=status.HTTP_401_UNAUTHORIZED)
    

@app.post("/upload_pdf")
async def upload(request: Request, date: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validate the format if needed
    try:
        datetime.strptime(date, "%Y-%m")
    except ValueError:
        return JSONResponse(content={"error": "Invalid date format. Use YYYY-MM."}, status_code=400)
    
    # Determine file extension
    file_extension = file.filename.split('.')[-1].lower()

    if file_extension == 'pdf':
        pdf_content = await file.read()  # Read PDF content as bytes

        # Save the PDF content to the database
        new_invoice = Invoice(month=date, invoice_pdf=pdf_content, invoice_filename=file.filename)
        db.add(new_invoice)
        db.commit()

        return templates.TemplateResponse("upload_excel.html", {"request": request, "successes": "PDF file uploaded and link saved successfully!"})
    
    elif file_extension in ['xls', 'xlsx', 'csv']:
        excel_content = await file.read()  # Read Excel content as bytes

        # Save the Excel content to the database (assuming you want to handle it similarly)
        new_invoice = Invoice(month=date, invoice_pdf=excel_content, invoice_filename=file.filename)
        db.add(new_invoice)
        db.commit()

        return templates.TemplateResponse("upload_excel.html", {"request": request, "successes": "Excel file uploaded and link saved successfully!"})
    else:
        return JSONResponse(content={"error": "Unsupported file type. Only PDF and Excel files are allowed."}, status_code=400)

    
    
@app.post("/upload")
async def upload(request: Request, date: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    
    # Validate the format if needed
    try:
        datetime.strptime(date, "%Y-%m")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM."}
    
    # Determine file extension
    file_extension = file.filename.split('.')[-1]

    # Handle Excel files
    if file_extension in ['xls', 'xlsx', 'csv']:
        
        # Save the date in the database
        new_entry = Finance(month=date)
        db.add(new_entry)
        db.flush()

        # Read the Excel file
        df = pd.read_excel(file.file)

        # Normalize column names
        columns = [col.strip().lower() for col in df.columns]
        print("Normalized column names:", columns)  # Debugging line

        # Define possible column name variations with regex patterns
        column_mappings = {
            'transaction id': ['transaction id', 'tran id'],
            'value date': ['value date', 'val date'],
            'transaction date': ['transaction date', 'trans date'],
            'transaction posted date': ['transaction posted date', 'trans posted date'],
            'cheque. no./ref. no.': ['cheque. no./ref. no.', 'cheq. no./ref. no.'],
            'transaction remarks': ['transaction remarks', 'trans remarks'],
            'deposit amt (inr)': ['deposit amt (inr)', 'deposit amt'],
            'withdrawal amt (inr)': ['withdrawal amt (inr)', 'withdrawal amt'],
            'balance (inr)': ['balance (inr)', 'balance']
        }

        # Match columns to their corresponding normalized names using regex patterns
        matched_columns = {}
        for key, variations in column_mappings.items():
            for variation in variations:
                closest_match = get_close_matches(variation, df.columns, n=1, cutoff=0.7)  # Adjust cutoff for more or less strict matching
                if closest_match:
                    matched_columns[key] = closest_match[0]
                    break

        # Check if all required columns are present
        required_columns = ['transaction id', 'value date', 'transaction date', 
                            'transaction posted date', 'cheque. no./ref. no.', 
                            'transaction remarks', 'deposit amt (inr)', 
                            'withdrawal amt (inr)', 'balance (inr)']

        if all(col in matched_columns for col in required_columns):
            transaction_id_col = matched_columns['transaction id']
            value_date_col = matched_columns['value date']
            transaction_date_col = matched_columns['transaction date']
            transaction_posted_date_col = matched_columns['transaction posted date']
            cheque_no_col = matched_columns['cheque. no./ref. no.']
            transaction_remarks_col = matched_columns['transaction remarks']
            deposit_amt_col = matched_columns['deposit amt (inr)']
            withdrawal_amt_col = matched_columns['withdrawal amt (inr)']
            balance_col = matched_columns['balance (inr)']

            total_revenue_amount = 0
            total_expenses_amount = 0

            # Iterate over the rows to populate the Finance table
            for _, row in df.iterrows():
                transaction_id = row[transaction_id_col] if pd.notnull(row[transaction_id_col]) else None
                value_date = row[value_date_col] if pd.notnull(row[value_date_col]) else None
                transaction_date = row[transaction_date_col] if pd.notnull(row[transaction_date_col]) else None
                transaction_posted_date = row[transaction_posted_date_col] if pd.notnull(row[transaction_posted_date_col]) else None
                cheque_no = row[cheque_no_col] if pd.notnull(row[cheque_no_col]) else None
                transaction_remarks = row[transaction_remarks_col] if pd.notnull(row[transaction_remarks_col]) else None
                withdrawal_amt = row[withdrawal_amt_col] if pd.notnull(row[withdrawal_amt_col]) else None
                deposit_amt = row[deposit_amt_col] if pd.notnull(row[deposit_amt_col]) else None
                balance = row[balance_col] if pd.notnull(row[balance_col]) else None

                # Convert withdrawal_amt and deposit_amt to float, handling errors
                try:
                    withdrawal_amt = float(withdrawal_amt) if withdrawal_amt else None
                except ValueError:
                    withdrawal_amt = None  # Set to None if conversion fails

                try:
                    deposit_amt = float(deposit_amt) if deposit_amt else None
                except ValueError:
                    deposit_amt = None  # Set to None if conversion fails

                # Summing up for calculations
                total_revenue_amount += deposit_amt if deposit_amt is not None else 0
                total_expenses_amount += withdrawal_amt if withdrawal_amt is not None else 0

                # Debugging prints to check the values
                print(f"Processing row with transaction_id='{transaction_id}', transaction_remarks='{transaction_remarks}', deposit_amt={deposit_amt}, withdrawal_amt={withdrawal_amt}")

                new_transaction = Finance(
                    month=date,
                    transaction_id=transaction_id,
                    value_date=value_date,
                    transaction_date=transaction_date,
                    transaction_posted_date=transaction_posted_date,
                    cheque_no_ref_no=cheque_no,
                    transaction_remarks=transaction_remarks,
                    withdrawal_amt=withdrawal_amt,
                    deposit_amt=deposit_amt,
                    balance=balance
                )
                db.add(new_transaction)

            db.commit()

            # Calculating profit, tax, and cess
            profit = total_revenue_amount - total_expenses_amount
            tax = profit * 0.25
            cess = tax * 0.4
            total_tax = tax + cess
            profit_after_tax = profit - total_tax

            # Save the calculation to the database
            new_calculation = Calculation(
                month=date,
                profit=profit,
                tax=tax,
                cess=cess,
                total_tax=total_tax,
                profit_after_tax=profit_after_tax
            )
            db.add(new_calculation)
            db.commit()

            # Return a success message in the template
            return templates.TemplateResponse("upload_excel.html", {"request": request, "success": "Excel file uploaded successfully!"})
        else:
            return templates.TemplateResponse("upload_excel.html", {"request": request, "error": "The required columns were not found in the uploaded file."})



@app.post("/add-expense-category", response_model=ExpenseCategory)
async def add_expense_category(expense: ExpenseCategory, db: Session = Depends(get_db)):
    existing_expense = db.query(Expenses).filter(Expenses.expense == expense.expense).first()
    if existing_expense:
        raise HTTPException(status_code=400, detail="Expense category already exists")
    
    new_expense = Expenses(expense=expense.expense)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

@app.get("/get-expense-categories", response_model=List[str])
async def get_expense_categories(db: Session = Depends(get_db)):
    expense_categories = db.query(Expenses.expense).all()
    return [category.expense for category in expense_categories]

@app.post("/submit-expense")
async def submit_expense(request: Request, db: Session = Depends(get_db), expense: str = Form(...)):
    expense_data = ExpenseCategory(expense=expense)
    await add_expense_category(expense_data, db)
    return RedirectResponse(url="/search/", status_code=303)


@app.get("/invoices")
async def get_invoices(db: Session = Depends(get_db), date: str = Query(...)):
    invoices = db.query(Invoice.id, Invoice.invoice_filename).filter(Invoice.month == date).all()
    invoices_list = [[invoice.id, invoice.invoice_filename] for invoice in invoices]
    return JSONResponse(content=invoices_list)


@app.get("/invoice/{invoice_filename}")
async def view_invoice(invoice_filename: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.invoice_filename == invoice_filename).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    file_extension = invoice.invoice_filename.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        media_type = "application/pdf"
    elif file_extension in {'xlsx', 'xls', 'xlsm'}:
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    return StreamingResponse(BytesIO(invoice.invoice_pdf), media_type=media_type, headers={
        "Content-Disposition": f'inline; filename="{invoice.invoice_filename}"'
    })


@app.post("/data_table", response_class=HTMLResponse)
async def data_table(request: Request, date: str = Form(...), db: Session = Depends(get_db)):
    print(f"Received date: {date}")

    rows = db.query(Finance).filter(Finance.month == date)
    
    revenues = []
    loans = []
    expenses = []

    total_revenue_amount = 0.0
    total_loan_amount = 0.0
    total_expenses_amount = 0.0

    for row in rows:
        remark = row.transaction_remarks
        deposit_amount = row.deposit_amt
        withdrawal_amount = row.withdrawal_amt
        transaction_date = row.transaction_date
        if isinstance(transaction_date, datetime):
            transaction_date = transaction_date.strftime('%d-%m-%Y')
        # elif isinstance(transaction_date, str):
        #     transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y')
            
        transaction_id = row.transaction_id
        expense_category = row.expenses if row.expenses is not None else ''
        invoice_data = json.loads(row.invoices_filename) if row.invoices_filename else []

        if isinstance(remark, str):
            if deposit_amount is not None:
                if "loan" not in remark.lower():
                    revenues.append((remark, deposit_amount, transaction_date, transaction_id, invoice_data))
                    try:
                        deposit_value = float(deposit_amount)
                        total_revenue_amount += deposit_value
                    except ValueError:
                        print(f"Invalid deposit amount '{deposit_amount}' in row {row}")

                else:
                    loans.append((remark, deposit_amount, transaction_date))
                    try:
                        deposit_value = float(deposit_amount)
                        total_loan_amount += deposit_value
                    except ValueError:
                        print(f"Invalid deposit amount '{deposit_amount}' in row {row}")

            if withdrawal_amount is not None:
                expenses.append((remark, withdrawal_amount, transaction_date, transaction_id, expense_category, invoice_data))
                try:
                    withdrawal_value = float(withdrawal_amount)
                    total_expenses_amount += withdrawal_value
                except ValueError:
                    print(f"Invalid withdrawal amount '{withdrawal_amount}' in row {row}")

    profit = total_revenue_amount - total_expenses_amount
    tax = profit * 0.25
    cess = tax * 0.4
    totalTax = tax + cess
    profit_after_tax = profit - totalTax

    context = {
        "request": request,
        "date": date,
        "revenues": revenues,
        "total_revenue_amount": total_revenue_amount,
        "loans": loans,
        "total_loan_amount": total_loan_amount,
        "expenses": expenses,
        "total_expenses_amount": total_expenses_amount,
        "profit": profit,
        "profit_after_tax": profit_after_tax,
        "tax": tax,
        "cess": cess,
        "totalTax": totalTax
    }

    print(context)

    return templates.TemplateResponse("data_table.html", context)


  
@app.post("/save-transaction", response_class=HTMLResponse)
async def save_transaction(request: Request, transaction_id: str = Form(...), expense_category: str = Form(None), invoice_category: List[str] = Form(None), db: Session = Depends(get_db)):
    # Retrieve the transaction from the database
    transaction = db.query(Finance).filter(Finance.transaction_id == transaction_id).first()
    
    if not transaction:
        return {"error": "Transaction not found."}

    # Update expense category if provided
    if expense_category is not None:
        transaction.expenses = expense_category if expense_category != "Select Exp" else None

    # Update invoices if provided
    if invoice_category is not None:
        # Fetch the selected invoices
        selected_invoices = db.query(Invoice).filter(Invoice.id.in_(invoice_category)).all()
        
        # Serialize the invoice data for saving in the Finance table
        serialized_invoices = [invoice.invoice_filename for invoice in selected_invoices]
        transaction.invoices_filename = json.dumps(serialized_invoices)

    db.commit()

    # Fetch the month from the updated transaction to ensure correct context
    date = transaction.month

    # Fetch all relevant data again to pass back to the template
    rows = db.query(Finance).filter(Finance.month == date).all()

    revenues = []
    loans = []
    expenses = []

    total_revenue_amount = 0.0
    total_loan_amount = 0.0
    total_expenses_amount = 0.0

    for row in rows:
        remark = row.transaction_remarks
        deposit_amount = row.deposit_amt
        withdrawal_amount = row.withdrawal_amt
        transaction_date = row.transaction_date
        if isinstance(transaction_date, datetime):
            transaction_date = transaction_date.strftime('%d-%m-%Y')
        elif isinstance(transaction_date, str):
            transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y')
            
        expense_category = row.expenses if row.expenses is not None else ''
        
        invoice_data = json.loads(row.invoices_filename) if row.invoices_filename else []

        if isinstance(remark, str):
            if deposit_amount is not None:
                if "loan" not in remark.lower():
                    revenues.append((remark, deposit_amount, transaction_date, row.transaction_id, invoice_data))
                    try:
                        deposit_value = float(deposit_amount)
                        total_revenue_amount += deposit_value
                    except ValueError:
                        print(f"Invalid deposit amount '{deposit_amount}' in row {row}")

                else:
                    loans.append((remark, deposit_amount, transaction_date))
                    try:
                        deposit_value = float(deposit_amount)
                        total_loan_amount += deposit_value
                    except ValueError:
                        print(f"Invalid deposit amount '{deposit_amount}' in row {row}")

            if withdrawal_amount is not None:
                expenses.append((remark, withdrawal_amount, transaction_date, row.transaction_id, expense_category, invoice_data))
                try:
                    withdrawal_value = float(withdrawal_amount)
                    total_expenses_amount += withdrawal_value
                except ValueError:
                    print(f"Invalid withdrawal amount '{withdrawal_amount}' in row {row}")

    profit = total_revenue_amount - total_expenses_amount
    tax = profit * 0.25
    cess = tax * 0.4
    totalTax = tax + cess
    profit_after_tax = profit - totalTax      

    return templates.TemplateResponse("data_table.html", {
        "request": request,
        "date": date,
        "revenues": revenues,
        "total_revenue_amount": total_revenue_amount,
        "loans": loans,
        "total_loan_amount": total_loan_amount,
        "expenses": expenses,
        "total_expenses_amount": total_expenses_amount,
        "profit": profit,
        "profit_after_tax": profit_after_tax,
        "tax": tax,
        "cess": cess,
        "totalTax": totalTax,
        "success": "Transaction updated successfully!"
    })



@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # Query all records from the Calculation table
    calculation_records = db.query(Calculation).all()

    # Calculate totals
    total_profit = 0.0
    total_tax = 0.0
    total_cess = 0.0
    total_total_tax = 0.0
    total_profit_after_tax = 0.0

    for record in calculation_records:
        try:
            total_profit += float(record.profit)
            total_tax += float(record.tax)
            total_cess += float(record.cess)
            total_total_tax += float(record.total_tax)
            total_profit_after_tax += float(record.profit_after_tax)
        except ValueError:
            print(f"Invalid value encountered in record {record.id}")

    context = {
        "request": request,
        "calculation_records": calculation_records,
        "total_profit": total_profit,
        "total_tax": total_tax,
        "total_cess": total_cess,
        "total_total_tax": total_total_tax,
        "total_profit_after_tax": total_profit_after_tax,
    }

    return templates.TemplateResponse("dashboard.html", context)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
