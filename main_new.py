import os
import pandas as pd
import numpy as np
import gradio as gr

# Read CSV
def read_bill_csv():
    bill_excel_path = os.path.join(os.getcwd(), "bills_input", "bills_input.xlsx")
    df = pd.read_excel(bill_excel_path, header=0)
    df.columns = ["item_name", "price"]
    return df

# Update involvement matrix based on checkbox selections
def add_cont_cols(df_state, people_state):
    """
    Add _cont columns for each person in the df
    """
    # print(f"people state type: {type(people_state)}")
    # print(f"people state: {people_state}")
    for p in people_state:
        df_state[p+"_cont"] = np.zeros(len(df_state))  # "_cont" suffix signifies the contribution (1: involved; 0: not involved)
    # print(f"df_head(): {df_state.head()}")
    return df_state


def calculate_value(cont_bool, price):
    cont_bool = np.array(cont_bool)
    per_person_value = price / np.sum(cont_bool) if np.sum(cont_bool) > 0 else 0
    value = -1 * per_person_value * cont_bool
    return value


def add_value_cols(df_state, people_state):
    """
    Add _value columns for all people
    """
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

# Generate debt summary
def generate_debt_df(df_state, df_debt_state, people_state, payer_state, item_count_state):
    """
    Create the debt table to show how much is owed by who to the payer
    """

    if len(df_state) - 1 > item_count_state:
        return df_debt_state, 0

    value_cols = [p+"_value" for p in people_state]
    debt_dict = dict(zip(people_state, list(df_state.loc[:, value_cols].sum())))
    for i, p in enumerate(people_state):
        if p != payer_state:
            df_debt_state.loc[i, ["people", "amount_owed"]] = [p, debt_dict[p]*-1]

    total_amount_owed = df_debt_state.amount_owed.sum()

    # total_amount_owed_str = f"Total amount owed to {payer_state} is: {total_amount_owed}"

    print(f"debug generate_debt_df: Total amount owed: {total_amount_owed}")
    print(f"debug generate_debt_df: debt_matrix: {df_debt_state}")
    
    return df_debt_state, total_amount_owed

with gr.Blocks() as demo:

    people_state = gr.State([])
    payer_state = gr.State("")

    gr.Markdown("### Enter the names of the people involved separated by a comma")
    
    # Step 2: Get people involved
    def get_names(names_in):
        names_in = names_in.split(",")
        people_inputs = [x.strip() for x in names_in]
        out = ", ".join(people_inputs)
        # print(f"out: {out}")
        # print(f"people_inputs: {people_inputs}")
        return out, people_inputs

    def payer_select(name_output):
        name_output = name_output.split(",")
        name_output = [x.strip() for x in name_output]
        return gr.update(choices=name_output, visible=True)

    def show_payer(payer_name):
        out = f"{payer_name}"
        return out, out
    
    people_textbox = gr.Textbox(label="Enter names (comma-separated):", interactive=True)
    submit_btn = gr.Button("Submit People Names")
    name_output = gr.Textbox(label="People involved in the shopping", render=True)

    payer_drop = gr.Dropdown(choices=[], label="Select the payer", visible=True)
    payer_text = gr.Textbox(label="Payer is:")

    item_count_state = gr.State(0)
    df_state = gr.State(read_bill_csv())
    df_debt = pd.DataFrame(columns = ["people", "amount_owed"])
    df_debt_state = gr.State(df_debt)
    amount_owed_state = gr.State(0)

    submit_btn.click(get_names, inputs=people_textbox, outputs=[name_output, people_state]).then(
        add_cont_cols, inputs = [df_state, people_state],  outputs = df_state)
    name_output.change(payer_select, inputs=name_output, outputs=payer_drop)
    payer_drop.change(show_payer, inputs=payer_drop, outputs=[payer_text, payer_state])

    gr.Markdown("### Enter who was involved in which item purchase")
    start_involvement = gr.Button("start entering involvement")

    def get_people_names_from_state(people_state):
        """
        Does what it says on the tin
        """
        return people_state
    
    def all_items_entered_check(df_state, item_count_state):
        if len(df_state) - 1 > item_count_state:
            items_pending = len(df_state) - 1 - item_count_state
            return f"{items_pending} Items pending ⚠️...Enter all items before proceeding"
        else:
            return "Click on 'Get final amount owed' button below to get the amount owed to the payer of the bill by the others"
                                    
    def get_item_details(df_state, item_count_state):
        # print(f"debug get_item_details:   df_state head: {df_state.head()}")
        # print(f"debug get_item_details:   item_count_state: {item_count_state}")
        # print(f"debug get_item_details:   item_name: {df_state.loc[item_count_state, ['item_name']].values}")
        # print(f"debug get_item_details:   item_price: {df_state.loc[item_count_state, ['price']].values}")
        if item_count_state >= len(df_state):
            return "All items processed !"
        item_name, item_price = df_state.loc[item_count_state, ["item_name"]].values, df_state.loc[item_count_state, ["price"]].values
        return f"Item: {item_name[0]}; \t\t Price: {item_price[0]}"
    
    def assign_contribution(df_state, item_count_state, people_involved):
        """
        Changes the values to 1 for the _cont columns for the people involved in the df_state
        """
        if item_count_state >= len(df_state):
            return df_state
        people_involved = [p+"_cont" for p in people_involved]
        df_state.loc[item_count_state, people_involved] = 1
        return df_state
    
    def update_item_counter(df_state, item_count_state):
        return item_count_state + 1

    item_desc_tb = gr.Textbox(value = get_item_details, inputs = [df_state, item_count_state], label = "Item Description")
    people_selection = gr.CheckboxGroup(choices = [], label = "Select people involved in this item and press submit...once 'All items processed !' appears, click the Finish button")
    people_submit = gr.Button("Submit", render=True)
    finish = gr.Button("Finish", render = True)
    messages = gr.Textbox(label = "Error warnings:")
    start_involvement.click(get_item_details, inputs = [df_state, item_count_state], outputs = item_desc_tb).then(
    lambda people: gr.update(choices=people),
    inputs=people_state,
    outputs=people_selection)
    
    people_submit.click(assign_contribution, inputs=[df_state, item_count_state, people_selection], 
                        outputs=[df_state]).then(update_item_counter, inputs=[df_state, item_count_state], outputs=[item_count_state])

    
    finish.click(all_items_entered_check, inputs=[df_state, item_count_state], outputs=[messages]).then(add_value_cols, inputs = [df_state, people_state], outputs=[df_state]).then(
        generate_debt_df, inputs = [df_state, df_debt_state, people_state, payer_state, item_count_state], outputs = [df_debt_state, amount_owed_state]
    )

    get_debt_button = gr.Button(value = "Get final amount owed", render = True)

    # gr.DataFrame(label = "Debt Matrix", value = df_debt_state)

    # rendering function to check whether the df is being updated correctly
    @gr.render(inputs = [df_state, df_debt_state, amount_owed_state, payer_state], triggers = [get_debt_button.click])
    def show_df(df_state, df_debt_state, amount_owed_state, payer_state):
        amount_owed_box = gr.Textbox(label = "Total amount owed to payer by others 🤑🤑", value = f"{payer_state} will get: {amount_owed_state}", render = True)
        print(f"debug show_df: amount_owed_state: {amount_owed_state}")
        print(f"debug show_df: payer_state: {payer_state}")
        print(f"debug show_df: df_debt_state: {df_debt_state}")
        gr.Markdown("### Debt matrix")
        gr.DataFrame(df_debt_state, interactive=False, render = True)

        gr.Markdown("### Final overall DF")
        gr.DataFrame(df_state, interactive=False, render = True)
    

demo.launch()
