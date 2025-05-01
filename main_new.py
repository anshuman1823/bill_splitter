import os
import pandas as pd
import numpy as np
import gradio as gr

# Step 1: Read CSV
def read_bill_csv():
    bill_excel_path = os.path.join(os.getcwd(), "bills_input", "bills_input.xlsx")
    df = pd.read_excel(bill_excel_path, header=0)
    df.columns = ["item_name", "price"]
    return df

# Step 4: Update involvement matrix based on checkbox selections
def add_cont_cols(df_state, people_state):
    """
    Add _cont columns for each person in the df
    """
    df_state = gr.State(read_bill_csv())
    for p in people_state:
        df_state[p+"_cont"] = np.zeros(len(df_state))  # "_cont" suffix signifies the contribution (1: involved; 0: not involved)
    return df_state

# Step 5: Calculate value matrix
def calculate_value(cont_bool, price):
    cont_bool = np.array(cont_bool)
    per_person_value = price / np.sum(cont_bool) if np.sum(cont_bool) > 0 else 0
    value = -1 * per_person_value * cont_bool
    return value

def assign_value(df, people, payer):
    value_cols = [p + "_value" for p in people]
    cont_cols = [p + "_cont" for p in people]
    for p in people:
        df[p + "_value"] = 0
    for i in range(len(df)):
        cont_bool = df.loc[i, cont_cols].values
        price = df.loc[i, "price"]
        value_vector = calculate_value(cont_bool, price)
        df.loc[i, value_cols] = value_vector
    return df

# Step 6: Generate debt summary
def generate_debt_summary(df, people, payer):
    summary = {}
    for person in people:
        if person != payer:
            amount = df[person + "_value"].sum()
            summary[person] = round(amount, 2)
    return pd.DataFrame(list(summary.items()), columns=["Person", "Amount Owed"])

# Step 7: Total owed
def total_owed(debt_df):
    return f"Total Owed to Payer: {debt_df['Amount Owed'].sum():.2f}"

# Main Gradio interface
with gr.Blocks() as demo:

    people_state = gr.State([])
    payer_state = gr.State("")

    gr.Markdown("### Enter the names of the people involved separated by a comma")
    
    # Step 2: Get people involved
    def get_names(names_in):
        names_in = names_in.split(",")
        people_inputs = [x.strip() for x in names_in]
        out = ", ".join(people_inputs)
        return out, out

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

    # Involvement matrix UI update with people names
    df_state = gr.State(pd.DataFrame())

    submit_btn.click(get_names, inputs=people_textbox, outputs=[name_output, people_state]).then(
        add_cont_cols, inputs = [df_state, people_state],  outputs = df_state
    )
    name_output.change(payer_select, inputs=name_output, outputs=payer_drop)
    payer_drop.change(show_payer, inputs=payer_drop, outputs=[payer_text, payer_state])

    @gr.render(inputs = df_state, triggers = [submit_btn.click])
    def show_df(df_state):
        gr.DataFrame(value = df_state, interactive=False)

    # def create_involvement_matrix(df):
    #     for item in range(len(df)):
    #         print("\n\nChoose the contributors for this item:")
    #         print(df.loc[item, ["item_name", "price"]])
    #         contributors = ask_person()
    #         contributors = [x+"_cont" for x in contributors]
    #         df.loc[item, contributors] = 1
    #     return df


    # involvement_df = gr.Dataframe(interactive=False, label="Bill Items")

    # involvement_matrix = gr.Dataframe(
    #     label="Select People Involved Per Item",
    #     col_count=(1, "dynamic"),
    #     datatype=["str"],
    #     row_count=(3, "dynamic")
    # )

    # def setup_involvement(df, people):
    #     # Show items
    #     short_df = df[["item_name", "price"]].copy()
    #     # Set up checkbox selections
    #     involvement = [[] for _ in range(len(df))]
    #     return short_df, involvement

    # setup_btn = gr.Button("Setup Involvement Table")
    # setup_btn.click(setup_involvement, inputs=[df_state, people_state], outputs=[involvement_df, involvement_matrix])

    # # Step 5 & 6 & 7: Calculate values, debt, and summary
    # final_df = gr.Dataframe(label="Value Assignment Table")
    # debt_table = gr.Dataframe(label="Amount Owed to Payer")
    # total_owed_text = gr.Textbox(label="Total Owed", interactive=False)

    # def full_update(df, involvement, people, payer):
    #     df = update_involvement(df.copy(), involvement, people)
    #     df = assign_value(df, people, payer)
    #     debt_df = generate_debt_summary(df, people, payer)
    #     total = total_owed(debt_df)
    #     return df, debt_df, total, df

    # update_btn = gr.Button("Update Calculations")
    # update_btn.click(full_update,
    #                  inputs=[df_state, involvement_matrix, people_state, payer_state],
    #                  outputs=[final_df, debt_table, total_owed_text, df_state])

demo.launch()
