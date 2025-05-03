import os
import pandas as pd
import numpy as np
import gradio as gr
import re
from ocr import extract_text_from_bill

def save_bill_excel(df):
    df.to_excel(os.path.join(os.getcwd(), "bills_input", "bills_input.xlsx"), index=False)
    return None

bill_txt_path = os.path.join(os.getcwd(), "bills_input", "bill_input_text.txt")

def extract_bill_items(file_path=bill_txt_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        bill = file.read()

    lines = bill.strip().split('\n')
    items = []
    prices = []

    for line in lines:
        item_match = re.match(r'^([\sa-zA-Z\\\/\,\']+|([\d]+[\sa-zA-z\\\/\,\']+))', line)
        if item_match:
            items.append(item_match.group())
            continue

        price_match = re.match(r'^(\d+\.\d+)\s*[\wА]*', line)
        if price_match:
            prices.append(price_match.group(1))

    table = [{'Item': item, 'Price': price} for item, price in zip(items, prices)]
    
    df = pd.DataFrame(table, columns=["Item", "Price"])
    save_bill_excel(df)

    return df

def update_dataframe(df):
    costs = np.array(df["Price"].apply(lambda x: float(x) if x != "" else 0))
    total = np.sum(costs)
    save_bill_excel(df)
    return total

def read_bill_csv():
    bill_excel_path = os.path.join(os.getcwd(), "bills_input", "bills_input.xlsx")
    df = pd.read_excel(bill_excel_path, header=0)
    df.columns = ["item_name", "price"]
    return df

def add_cont_cols(df_state, people_state):
    for p in people_state:
        df_state[p+"_cont"] = np.zeros(len(df_state))
    return df_state

def calculate_value(cont_bool, price):
    cont_bool = np.array(cont_bool)
    per_person_value = price / np.sum(cont_bool) if np.sum(cont_bool) > 0 else 0
    value = -1 * per_person_value * cont_bool
    return value

def add_value_cols(df_state, people_state):
    value_cols = [p+"_value" for p in people_state]
    cont_cols = [p+"_cont" for p in people_state]

    for p in people_state:
        df_state[p+"_value"] = np.zeros(len(df_state))
    
    for i in range(len(df_state)):
        cont_bool = df_state.loc[i, cont_cols].values
        price = df_state.loc[i, "price"]
        value_vector = calculate_value(cont_bool, price)
        df_state.loc[i, value_cols] = value_vector

    return df_state

def generate_debt_df(df_state, df_debt_state, people_state, payer_state, item_count_state):
    if len(df_state) - 1 > item_count_state:
        return df_debt_state, 0

    value_cols = [p+"_value" for p in people_state]
    debt_dict = dict(zip(people_state, list(df_state.loc[:, value_cols].sum())))
    for i, p in enumerate(people_state):
        if p != payer_state:
            df_debt_state.loc[i, ["people", "amount_owed"]] = [p, debt_dict[p]*-1]

    total_amount_owed = df_debt_state.amount_owed.sum()
    return df_debt_state, total_amount_owed

def save_text_file(text, path = bill_txt_path):
    """
    Save the passed text as a text file
    """
    if path is None:
        path = os.path.join(os.getcwd(), "bills_input", "bill_input_text.txt")
    
    if text is None:
        print(f"Bill text passed to save_text_file function is None")
    else:
        with open(path, "w") as file:
            file.write(text)

def update_ocr_input():
    df = extract_bill_items()
    return gr.update(value = df)

# def assign_supermarket(supermarket):
#     return supermarket
    
# def assign_bill_date(date):
#     return date

with gr.Blocks() as app:

    with gr.Tab("Read Bill"):
        ocr_textbox = gr.Textbox(label = "Text captured from the bil via OCR", interactive = True)
        gr.Interface(fn = extract_text_from_bill, inputs=["image"], outputs = [ocr_textbox])
        
        save_bill_text_button = gr.Button(value = "Save OCR Text")
        save_bill_text_button.click(fn=save_text_file, inputs = ocr_textbox)

    # supermarket_state = gr.State("")
    # bill_date_state = gr.State("")

    with gr.Tab("Process Bill"):

        df_bill = extract_bill_items()
    
        gr.Markdown("# Make changes to the input items/cost")
        gr.Markdown("### Guide:")
        gr.Markdown("#### Press 'Submit/View-Total' to view the total bill cost")
        gr.Markdown("#### ⚠️ Also press 'Submit/View-Total' button after making any changes to Save the changes ⚠️ ")
        gr.Markdown("#### Press 'Refresh' to refresh the ocr text input")
        gr.Markdown("#### When done, proceed to the next tab 'Bill Splitter'")
        
        refresh_button = gr.Button(value = "Refresh OCR input")
        
        dataframe = gr.Dataframe(
            headers=["Item", "Cost"],
            datatype=["str", "number"],
            interactive=True,
            row_count=(len(df_bill), "dynamic"),
            col_count=(2, "fixed"),
            value=df_bill,
        )

        refresh_button.click(update_ocr_input, outputs = dataframe)

        sum_textbox = gr.Textbox(label="Total bill Cost", interactive=False)
        submit_btn = gr.Button("Submit/View-Total")

        submit_btn.click(
            update_dataframe,
            inputs=[dataframe],
            outputs=[sum_textbox],
        )

    with gr.Tab("Bill Splitter"):
        people_state = gr.State([])
        payer_state = gr.State("")

        gr.Markdown("### Enter the names of the people involved separated by a comma")
        
        def get_names(names_in):
            names_in = names_in.split(",")
            people_inputs = [x.strip() for x in names_in]
            out = ", ".join(people_inputs)
            return out, people_inputs

        def payer_select(name_output):
            name_output = name_output.split(",")
            name_output = [x.strip() for x in name_output]
            return gr.update(choices=name_output, visible=True)

        def show_payer(payer_name):
            out = f"{payer_name}"
            return out, out
        
        def read_bill(df_state):
            df_state = read_bill_csv()
            return df_state
        
        people_textbox = gr.Textbox(label="Enter names (comma-separated):", interactive=True)
        restart_button = gr.Button(value = "Restart-Entry")
        gr.Markdown("#### Note: Remember to reselect the payer from the dropdown after pressing Restart-Entry")
        submit_btn = gr.Button("Submit People Names")
        name_output = gr.Textbox(label="People involved in the shopping", render=True)

        payer_drop = gr.Dropdown(choices=[], label="Select the payer", visible=True)
        payer_text = gr.Textbox(label="Payer is:")

        item_count_state = gr.State(0)
        df_state = gr.State(read_bill_csv())
        df_debt = pd.DataFrame(columns=["people", "amount_owed"])
        df_debt_state = gr.State(df_debt)
        amount_owed_state = gr.State(0)

        submit_btn.click(get_names, inputs=people_textbox, outputs=[name_output, people_state]).then(
                read_bill, inputs = [df_state], outputs=[df_state]).then(
                    add_cont_cols, inputs=[df_state, people_state], outputs=df_state)
        name_output.change(payer_select, inputs=name_output, outputs=payer_drop)
        payer_drop.change(show_payer, inputs=payer_drop, outputs=[payer_text, payer_state])

        restart_button.click(read_bill, inputs = [df_state], outputs = [df_state]).then(
            lambda x: 0, inputs = item_count_state, outputs=item_count_state).then(
                lambda x:[], inputs = people_state, outputs=people_state).then(
                    # lambda x:"", inputs = payer_state, outputs = payer_state).then(
                        lambda x: pd.DataFrame(columns=["people", "amount_owed"]), inputs = df_debt_state, outputs=df_debt_state).then(
                            lambda x: read_bill_csv(), inputs=df_state, outputs=df_state)

        gr.Markdown("### Enter who was involved in which item purchase")
        start_involvement = gr.Button("start entering involvement")

        def get_item_details(df_state, item_count_state):
            if item_count_state >= len(df_state):
                return "All items processed !"
            item_name, item_price = df_state.loc[item_count_state, ["item_name"]].values, df_state.loc[item_count_state, ["price"]].values
            return f"Item: {item_name[0]}; \t\t Price: {item_price[0]}"
        
        def assign_contribution(df_state, item_count_state, people_involved):
            if item_count_state >= len(df_state):
                return df_state
            people_involved = [p+"_cont" for p in people_involved]
            df_state.loc[item_count_state, people_involved] = 1
            return df_state
        
        def update_item_counter(item_count_state):
            return item_count_state + 1
        
        def all_items_entered_check(df_state, item_count_state):
            if len(df_state) - 1 > item_count_state:
                items_pending = len(df_state) - 1 - item_count_state
                return f"{items_pending} Items pending ⚠️...Enter all items before proceeding"
            else:
                return "Click on 'Get final amount owed' button below to get the amount owed to the payer of the bill by the others"
        
        def save_df(df_state):
            """
            Save the final df_state df as excel file in the cwd under "final_table.xlsx" name
            """
            df_state.to_excel("final_table.xlsx", index = False)

        item_desc_tb = gr.Textbox(value=get_item_details, inputs=[df_state, item_count_state], label="Item Description")
        people_selection = gr.CheckboxGroup(choices=[], label="Select people involved in this item and press submit...once 'All items processed !' appears, click the Finish button")
        people_submit = gr.Button("Submit", render=True)
        finish = gr.Button("Finish", render=True)
        messages = gr.Textbox(label="Error warnings:")
        
        start_involvement.click(get_item_details, inputs=[df_state, item_count_state], outputs=item_desc_tb).then(
            lambda people: gr.update(choices=people),
            inputs=people_state,
            outputs=people_selection)
        
        people_submit.click(assign_contribution, inputs=[df_state, item_count_state, people_selection], 
                            outputs=[df_state]).then(update_item_counter, inputs=item_count_state, outputs=item_count_state)

        finish.click(all_items_entered_check, inputs=[df_state, item_count_state], outputs=[messages]).then(add_value_cols, inputs=[df_state, people_state], outputs=[df_state]).then(
            generate_debt_df, inputs=[df_state, df_debt_state, people_state, payer_state, item_count_state], outputs=[df_debt_state, amount_owed_state]
        )

        get_debt_button = gr.Button(value="Get final amount owed", render=True)
        
        get_debt_button.click(save_df, inputs = [df_state], outputs = [])

        @gr.render(inputs=[df_state, df_debt_state, amount_owed_state, payer_state], triggers=[get_debt_button.click])
        def show_df(df_state, df_debt_state, amount_owed_state, payer_state):
            amount_owed_box = gr.Textbox(label="Total amount owed to payer by others 🤑🤑", value=f"{payer_state} will get: {amount_owed_state}", render=True)
            gr.Markdown("### Debt matrix")
            gr.DataFrame(df_debt_state, interactive=False, render=True)

            gr.Markdown("### Final overall DF")
            gr.DataFrame(df_state, interactive=False, render=True)

app.launch()