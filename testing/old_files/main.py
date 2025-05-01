import os
import pandas as pd
import numpy as np
import gradio as gr

cwd = os.getcwd()  # Get the current working directory (cwd)

def read_bill_csv():
    """
    This function reads the bill csv generated after parsing the bill image
    """
    bill_excel_path = os.path.join(os.getcwd(), "bills_input", "bills_input.xlsx")
    columns = ["item_name", "price"]
    df = pd.read_excel(bill_excel_path, header = 0)
    df.columns = columns
    return df

df = read_bill_csv()

def ask_people_involved():
    """
    Asks who the people involved in the bill are
    """
    print("\n\nEnter the people who are involved in the bill...press enter to stop")
    p = " "
    people = []
    while p != "":
        p = input("Enter name of person involved:  ")
        if p != "":
            people.append(p)

    if len(people) == 0:
        raise ValueError("No one involved????")
    return people

people = ask_people_involved()

def ask_person():
    print(people)
    choice = input("\n\nChoose person from the given list (index starts from 1): \n To choose multiple separate the indices with comma")
    choice = choice.split(",")
    choice = [int(x.strip()) - 1 for x in choice]
    return [people[x] for x in choice]

def ask_payer():
    print("\n\nChoose the payer of the bill (only a single payer allowed):")
    payer = ask_person()
    if len(payer) > 1:
        raise ValueError("multiple payers not allowed")
    return payer[0]

def create_involvement_matrix(df):
    for p in people:
        df[p+"_cont"] = np.zeros(len(df))  # "_cont" suffix signifies the contribution (1: involved; 0: not involved)

    for item in range(len(df)):
        print("\n\nChoose the contributors for this item:")
        print(df.loc[item, ["item_name", "price"]])
        contributors = ask_person()
        contributors = [x+"_cont" for x in contributors]
        df.loc[item, contributors] = 1
    return df

df = create_involvement_matrix(df)   

payer = ask_payer()  # name of the payer

cont_cols = [x+"_cont" for x in people] # cont_columns is the name of the columns like [p1_cont, p2_cont] (p1, p2 are people names)
value_cols = [p+"_value" for p in people] # value_columns is the name of the columns like [p1_value, p2_value] (p1, p2 are people names)

def calculate_value(cont_bool, price, people , payer):
    """
    Calculates the contribution of each person given an item and the people involved in it.
    Returns a list with positive values indicating money lent and negative values indicating money borrowed
    """
    cont_bool = np.array(cont_bool)
    
    if len(cont_bool) != len(people):
        print(f"cont_bool: {cont_bool}")
        print(f"people: {people}")
        raise ValueError("length of contribution vector not matching the number of people involved")
    
    per_person_value = price/np.sum(cont_bool)
    value = -1 * per_person_value * cont_bool
    # payer_index = people.index(payer)
    # value[payer_index] += price
    return value

def assign_value(df, payer = payer, cont_cols = cont_cols):
    for p in people:
        df[p+"_value"] = np.zeros(len(df))
    value_cols = [p+"_value" for p in people]
    for item in range(len(df)):
        cont_bool = list(df.loc[item, cont_cols].values)
        price = df.loc[item, ["price"]].values
        value_vector = calculate_value(cont_bool=cont_bool, price = price, people = people, payer = payer)
        df.loc[item, value_cols] = value_vector
    return df

df = assign_value(df)

def print_debts(df = df, value_cols = value_cols, payer = payer):
    """
    Print the final value of debts owed by each person
    """
    print("\n\n Final settlement (negative means that the person owes money to the payer)")
    for person in value_cols:
        name = person[:-6]   #-6 for removing suffix _value
        if name != payer:
            amount = df[person].sum()
            print(f"{name} owes {payer}: {amount}")

print_debts(df, value_cols, payer)
df.to_excel(os.path.join(os.getcwd(), "final_table.xlsx"))


