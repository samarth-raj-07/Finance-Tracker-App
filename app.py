import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

# Database Setup
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        amount REAL,
        description TEXT
    )
''')
conn.commit()

# Function to Add Transaction
def add_transaction():
    date = date_entry.get_date().strftime("%Y-%m-%d")
    category = category_var.get()
    amount = amount_entry.get()
    description = desc_entry.get()

    if not date or not category or not amount:
        messagebox.showwarning("Input Error", "Please fill all fields!")
        return

    try:
        cursor.execute("INSERT INTO transactions (date, category, amount, description) VALUES (?, ?, ?, ?)",
                       (date, category, float(amount), description))
        conn.commit()
        messagebox.showinfo("Success", "Transaction added successfully!")
        load_data()
        update_month_dropdown()
    except Exception as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")

# Function to Load Data for Selected Month
def load_data():
    selected_month = month_var.get()
    if not selected_month:
        messagebox.showwarning("Input Error", "Please select a month!")
        return

    cursor.execute("SELECT * FROM transactions WHERE strftime('%Y-%m', date) = ?", (selected_month,))
    rows = cursor.fetchall()

    for tree in (income_tree, expense_tree):
        for row in tree.get_children():
            tree.delete(row)

    total_income = 0
    total_expenses = {"Needs": 0, "Wants": 0, "Savings": 0}

    for row in rows:
        id_, date, category, amount, desc = row
        if category == "Income":
            income_tree.insert("", "end", values=( date, amount, desc), tags=("income_row",))
            total_income += amount
        else:
            expense_tree.insert("", "end", values=( date, category, amount, desc), tags=(category,))
            total_expenses[category] += amount

    total_income_label.config(text=f"Total Income: ₹{total_income}")
    total_expense_label.config(text=f"Total Expenses: ₹{sum(total_expenses.values())}")

    for row in summary_tree.get_children():
        summary_tree.delete(row)

    for cat, amt in total_expenses.items():
        percent = (amt / total_income * 100) if total_income else 0
        summary_tree.insert("", "end", values=(cat, amt, f"{percent:.2f}%"))

# Function to Populate Available Months in Dropdown
def update_month_dropdown():
    cursor.execute("SELECT DISTINCT strftime('%Y-%m', date) FROM transactions ORDER BY date DESC")
    months = [row[0] for row in cursor.fetchall()]
    
    if months:
        month_dropdown["values"] = months
        month_var.set(months[0])
    else:
        month_dropdown["values"] = []
        month_var.set("")

# Function to Delete a Transaction
def delete_transaction(tree):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a row to delete!")
        return

    row_id = tree.item(selected_item)['values'][0]

    try:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (row_id,))
        conn.commit()
        tree.delete(selected_item)
        load_data()
    except Exception as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")

# GUI Setup
root = tk.Tk()
root.title("Expense Tracker")
root.config(bg="#CEE6F2", bd=5, relief="ridge")
root.option_add("*Font", ("Arial", 12))
# root.attributes('-fullscreen', True)  # Always Open in Fullscreen

# Input Frame (Centered)
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

tk.Label(input_frame, text="Date:").grid(row=0, column=0)
date_entry = DateEntry(input_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
date_entry.grid(row=0, column=1)

tk.Label(input_frame, text="Category:").grid(row=0, column=2)
category_var = tk.StringVar()
category_dropdown = ttk.Combobox(input_frame, textvariable=category_var, values=["Income", "Needs", "Wants", "Savings"], state="readonly")
category_dropdown.grid(row=0, column=3)
category_dropdown.current(0)

tk.Label(input_frame, text="Amount:").grid(row=0, column=4)
amount_entry = tk.Entry(input_frame)
amount_entry.grid(row=0, column=5)

tk.Label(input_frame, text="Description:").grid(row=0, column=6)
desc_entry = tk.Entry(input_frame)
desc_entry.grid(row=0, column=7)

tk.Button(input_frame, text="Add Transaction", command=add_transaction).grid(row=0, column=8)

# Month Selection
month_frame = tk.Frame(root)
month_frame.pack(pady=5)

tk.Label(month_frame, text="Select Month:", bg= "#faebd7").pack(side=tk.LEFT)
month_var = tk.StringVar()
month_dropdown = ttk.Combobox(month_frame, textvariable=month_var, state="readonly")
month_dropdown.pack(side=tk.LEFT, padx=5)
tk.Button(month_frame, text="Load Data", command=load_data).pack(side=tk.LEFT, padx=5)


# Tables Frame (Grid Layout for Proper Sizing)
tables_frame = tk.Frame(root)
tables_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Income Table Frame
income_frame = tk.Frame(tables_frame)
income_frame.grid(row=0, column=0, padx=10, sticky="nsew")

tk.Label(income_frame, text="Income Table", bg="lightgreen", font=("Arial", 12, "bold")).pack(fill="both")

income_tree = ttk.Treeview(income_frame, columns=( "Date", "Amount", "Description"), show="headings", height=10)
income_tree.pack(expand=True, fill="both")

for col in ("Date", "Amount", "Description"):
    income_tree.heading(col, text=col)

income_tree.tag_configure("income_row", background="lightgreen")

tk.Button(income_frame, text="Delete Income Transaction", command=lambda: delete_transaction(income_tree)).pack(pady=5)

# Expense Table Frame
expense_frame = tk.Frame(tables_frame)
expense_frame.grid(row=0, column=1, padx=10, sticky="nsew")

tk.Label(expense_frame, text="Expense Table", bg="lightcoral", font=("Arial", 12, "bold")).pack(fill="both")

expense_tree = ttk.Treeview(expense_frame, columns=("Date", "Category", "Amount", "Description"), show="headings", height=10)
expense_tree.pack(expand=True, fill="both")

for col in ( "Date", "Category", "Amount", "Description"):
    expense_tree.heading(col, text=col)

expense_tree.tag_configure("Needs", foreground="blue")
expense_tree.tag_configure("Wants", foreground="red")
expense_tree.tag_configure("Savings", foreground="green")

tk.Button(expense_frame, text="Delete Expense Transaction", command=lambda: delete_transaction(expense_tree)).pack(pady=5)

# Ensure grid expands properly
tables_frame.columnconfigure(0, weight=1)
tables_frame.columnconfigure(1, weight=1)

# # Tables Frame (Side by Side)
# tables_frame = tk.Frame(root)
# tables_frame.pack(pady=10)
# tables_frame.config(bd=5, relief="ridge")

# # Income Table
# income_frame = tk.Frame(tables_frame)
# income_frame.pack(side=tk.LEFT, padx=20)

# tk.Label(income_frame, text="Income Table", bg="lightgreen", font=("Arial", 12, "bold")).pack(fill="both", expand=True)

# income_tree = ttk.Treeview(income_frame, columns=("ID", "Date", "Amount", "Description"), show="headings")
# income_tree.pack()

# for col in ("ID", "Date", "Amount", "Description"):
#     income_tree.heading(col, text=col)

# # ✅ Configure "income_row" tag for Green Background
# income_tree.tag_configure("income_row", background="lightgreen")

# tk.Button(income_frame, text="Delete Income Transaction", command=lambda: delete_transaction(income_tree)).pack(pady=5)

# # Expense Table
# expense_frame = tk.Frame(tables_frame)
# expense_frame.pack(side=tk.RIGHT, padx=20)

# tk.Label(expense_frame, text="Expense Table", bg="lightcoral", font=("Arial", 12, "bold")).pack(fill="both", expand=True)

# expense_tree = ttk.Treeview(expense_frame, columns=("ID", "Date", "Category", "Amount", "Description"), show="headings")
# expense_tree.pack()

# for col in ("ID", "Date", "Category", "Amount", "Description"):
#     expense_tree.heading(col, text=col)

# expense_tree.tag_configure("Needs", foreground="blue")
# expense_tree.tag_configure("Wants", foreground="red")
# expense_tree.tag_configure("Savings", foreground="green")

# tk.Button(expense_frame, text="Delete Expense Transaction", command=lambda: delete_transaction(expense_tree)).pack(pady=5)

# Total Income & Expenses
total_frame = tk.Frame(root)
total_frame.pack(pady=10)
total_income_label = tk.Label(total_frame, text="Total Income: ₹0", font=("Arial", 12, "bold"))
total_income_label.pack()
total_expense_label = tk.Label(total_frame, text="Total Expenses: ₹0", font=("Arial", 12, "bold"))
total_expense_label.pack()

# Summary Table
summary_frame = tk.Frame(root)
summary_frame.pack(pady=10)
summary_frame.config(bd=5, relief="ridge")
tk.Label(summary_frame, text="Summary Table", font=("Arial", 12, "bold")).pack()
summary_tree = ttk.Treeview(summary_frame, columns=("Category", "Amount", "Percentage"), show="headings")
summary_tree.pack()
for col in ("Category", "Amount", "Percentage"):
    summary_tree.heading(col, text=col)

update_month_dropdown()
load_data()

root.mainloop()
