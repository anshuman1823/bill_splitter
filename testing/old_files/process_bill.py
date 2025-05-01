import os
import pandas as pd
import gradio as gr
import numpy as np
import re

def save_bill_excel(df):
    """
    Takes the pandas df and saves it to a fixed location with a fixed name
    """
    df.to_excel(os.path.join(os.getcwd(), "bills_input", "bills_input.xlsx"), index=False)

# default bill text path
bill_txt_path = os.path.join(os.getcwd(), "bills_input", "bill_input_text.txt")

def extract_bill_items(file_path = bill_txt_path):
    
    with open(file_path, 'r', encoding='utf-8') as file:
        bill = file.read()

    lines = bill.strip().split('\n')
    # print(f"lines: {lines}")

    items = []
    prices = []

    for line in lines:
        item_match = re.match(r'^([\sa-zA-Z\\\/\,\']+|([\d]+[\sa-zA-z\\\/\,\']+))', line)
        if item_match:
            items.append(item_match.group())
            continue  # Skip further checks for this line

        price_match = re.match(r'^(\d+\.\d+)\s*[\wА]*', line)
        if price_match:
            prices.append(price_match.group(1))

    # Pair items and prices
    table = [{'Item': item, 'Price': price} for item, price in zip(items, prices)]
    
    print(f"items: {items}")
    print(f"prices: {prices}")

    df = pd.DataFrame(table, columns = ["Item", "Price"])
    save_bill_excel(df)

    return df


# Function to handle dataframe updates and return sum
def update_dataframe(df):
    # Ensure numerical column is numeric
    costs = np.array(df["Price"].apply(lambda x: float(x)))
    total = np.sum(costs)
    save_bill_excel(df)
    return total

with gr.Blocks() as bill_IF:
    df_bill = extract_bill_items()

    gr.Markdown("### Make changes to the input items/cost")
    dataframe = gr.Dataframe(
        headers=["Item", "Cost"],
        datatype=["str", "number"],
        interactive=True,
        label="Edit your items and costs...press submit to save get the updated total cost",
        row_count=(len(df_bill), "dynamic"),
        col_count=(2, "fixed"),
        value=df_bill,
    )

    sum_textbox = gr.Textbox(label="Total bill Cost", interactive=False)

    submit_btn = gr.Button("Submit Changes")

    submit_btn.click(
        update_dataframe,
        inputs=[dataframe],
        outputs=[sum_textbox],
    )

if __name__ == "__main__":
    bill_IF.launch()
