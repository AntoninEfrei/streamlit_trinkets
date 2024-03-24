import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
import json
import base64
st.set_page_config(layout="wide")

# Stylish header
st.markdown(
    """
    <h2 style='text-align: center; color: #f63366;'>Nexus Tour Reporting</h2>
    <hr style='margin-bottom: 20px;'>
    """,
    unsafe_allow_html=True
)


def load_data():
    return pd.read_csv("nexustour_etape1_raw_data.csv")


df = load_data()

df_dmg_gold = pd.read_csv('gold_dmg_ratio_etape1.csv')
df_dmg_gold.rename(columns={'avg':'Dmg/Gold Ratio'}, inplace = True)

page = st.sidebar.radio("Navigation", ("Nexus Tour Reporting","Team Focus","Player focus"))

if page == "Player focus":
    
    # Filter options
    riot_ids = df['riot_id'].unique()
    sides = ['red', 'blue']

    # Sidebar filters
    selected_riot_id = st.sidebar.selectbox("Select Riot ID", riot_ids)
    selected_side = st.sidebar.multiselect("Select Side", sides)

    # Apply filters
    filtered_df = df[df['riot_id'] == selected_riot_id]
    if selected_side:
        filtered_df = filtered_df[filtered_df['side'].isin(selected_side)]

    # Compute win rates
    win_rates = filtered_df.groupby('champion')['win'].agg(['mean', 'size'])  # Aggregate mean and count

    win_rates.columns = ['win_rate', 'nb_game']
    win_rates['win_rate'] = win_rates['win_rate']*100

    st.subheader('Champions Played')
    st.write(win_rates)

elif page == "Nexus Tour Reporting":

    available_dates = sorted(df['Date'].unique())
    selected_dates = st.sidebar.multiselect("Select Dates", available_dates, default=available_dates)

    # Create tabs for each role
    roles = ['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY']
    col1, col2,col3,col4,col5 = st.columns([5,5,5,5,5])
    columns = [col1,col2,col3,col4,col5]
    for role,col in zip(roles,columns):
        
        role_df = df[(df['team_position'] == role) & (df['Date'].isin(selected_dates))]
        win_rates = role_df.groupby('champion')['win'].agg(['mean', 'size'])  # Aggregate mean and count
        win_rates.columns = ['win_rate', 'nb_game']
        win_rates['win_rate'] = (win_rates['win_rate'] * 100).round(1)
        win_rates = win_rates.sort_values(by='nb_game', ascending = False)
        with col:
           st.write(f"### {role} ")
           st.write(win_rates)

elif page == 'Team Focus':
    
    sides = ['red', 'blue']

    # Buttons
    team_options = ['None'] + df['team'].unique().tolist()
    selected_team = st.sidebar.selectbox("Select Team",team_options)
    selected_side = st.sidebar.multiselect("Select Side", sides)

    if selected_team != 'None':
        # Apply filters for the team selected / side selected
        filtered_df = df[df['team'] == selected_team]
        if selected_side:
            filtered_df = filtered_df[filtered_df['side'].isin(selected_side)]
    
        # get list of nicknames & puuid of the selected ppl
        list_nicknames = filtered_df['riot_id'].unique().tolist()
        list_puuid = filtered_df['puuid'].unique().tolist()
    
        # get rentability for player
        df_dmg_gold_filtered = df_dmg_gold[df_dmg_gold['puuid'].isin(list_puuid)].reset_index(drop = True)
        df_dmg_gold_filtered['riot_id'] = list_nicknames
    
    
        roles = ['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY']
    
        # Pick History
        st.markdown('<h2 class="title">Pick History</h2>', unsafe_allow_html=True)
    
        col1, col2, col3, col4, col5 = st.columns([5, 5, 5, 5, 5])
        columns = [col1, col2, col3, col4, col5]
        col_nb = 0
        for role, col in zip(roles, columns):
            role_df = filtered_df[filtered_df['team_position'] == role]
            win_rates = role_df.groupby('champion')['win'].agg(['mean', 'size'])  # Aggregate mean and count
            win_rates.columns = ['win_rate', 'nb_game']
            win_rates['win_rate'] = (win_rates['win_rate'] * 100).round(2)
            win_rates = win_rates.sort_values(by='nb_game', ascending=False)
            with col:
                st.write(f"##### {role[0] + role[1:].lower()}: {list_nicknames[col_nb]}")
                st.write(win_rates)
                col_nb += 1
        st.markdown('</div>', unsafe_allow_html=True)
    
        # Rentability section
    
        st.markdown('<h2 class="title">Rentability</h2>', unsafe_allow_html=True)
        st.write('Rentability for each player (Gold/Dmg per minute)')
        st.write(df_dmg_gold_filtered[['riot_id', 'Dmg/Gold Ratio']])
    
     
        st.write(df)
    else : 
        st.write(' ## Choose a Team in the filter !')

