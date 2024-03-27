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
    # Load your dataframe & champs icons
    '''with open('nexus_tour/json/champion_icons.json', 'r') as json_file:
        champion_icons_base64 = json.load(json_file)
        champion_icons = {champion: base64.b64decode(icon) for champion, icon in champion_icons_base64.items()}
    '''
    return pd.read_csv("nexustour_etape1_raw_data.csv")#,champion_icons


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

    puuid = df[df['riot_id'] == selected_riot_id]['puuid'].unique()
    # Apply filters
    filtered_df = df[df['riot_id'] == selected_riot_id]
    if selected_side:
        filtered_df = filtered_df[filtered_df['side'].isin(selected_side)]
    st.write(filtered_df)
    

    # get Xpdiff for player
    avg_xpdiff = filtered_df.groupby('champion').agg({'xpdiff_at5': 'mean', 'xpdiff_at10': 'mean', 'xpdiff_at15': 'mean'}).reset_index()

    # Group by 'champion' again to count the number of games
    nb_game = filtered_df.groupby('champion').size().reset_index(name='nb_game')

    # Merge the two DataFrames on 'champion' column
    avg_xpdiff_by_champion = pd.merge(avg_xpdiff, nb_game, on='champion')
    avg_xpdiff_by_champion.set_index('champion', inplace = True)
    avg_xpdiff_by_champion = avg_xpdiff_by_champion.round(1)
    # Compute win rates
    win_rates = filtered_df.groupby('champion')['win'].agg(['mean', 'size'])  # Aggregate mean and count

    win_rates.columns = ['win_rate', 'nb_game']
    win_rates['win_rate'] = win_rates['win_rate']*100

    st.subheader('Champions Played')
    st.write(win_rates)
    
    st.write(avg_xpdiff_by_champion)

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
    
    roles = ['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY']
    # Buttons
    selected_team = st.sidebar.selectbox("Select Team", df['team'].unique())
    selected_side = st.sidebar.multiselect("Select Side", sides)

    # Apply filters for the team selected / side selected
    filtered_df = df[df['team'] == selected_team]

    if selected_side:
        filtered_df = filtered_df[filtered_df['side'].isin(selected_side)]

    # get list of nicknames & puuid of the selected ppl
    list_puuid = filtered_df['puuid'].unique().tolist()

    # get the most frequent team position to determine position of all players in the list nicknames
    most_frequent_positions = filtered_df.groupby('riot_id')['team_position'].agg(lambda x: x.value_counts().idxmax())
    riot_id_positions_dict = most_frequent_positions.to_dict()
    list_nicknames = sorted(riot_id_positions_dict.keys(), key=lambda x: roles.index(riot_id_positions_dict[x]))

    # get rentability for player
    df_dmg_gold_filtered = df_dmg_gold[df_dmg_gold['puuid'].isin(list_puuid)].reset_index(drop = True)
    df_dmg_gold_filtered['riot_id'] = list_nicknames
    df_dmg_gold_filtered['role'] = roles
    df_dmg_gold_filtered.set_index('role', inplace = True)

    # get Xpdiff for player
    avg_xpdiff_by_puuid = filtered_df.groupby('riot_id').agg({'xpdiff_at5': 'mean', 'xpdiff_at10': 'mean', 'xpdiff_at15': 'mean'}).reset_index()
    avg_xpdiff_by_puuid.rename(columns={'xpdiff_at5': 'xpdiff_at5_avg', 'xpdiff_at10': 'xpdiff_at10_avg', 'xpdiff_at15': 'xpdiff_at15_avg'}, inplace=True)
    avg_xpdiff_by_puuid['riot_id'] = pd.Categorical(avg_xpdiff_by_puuid['riot_id'], categories=list_nicknames, ordered=True)
    avg_xpdiff_by_puuid = avg_xpdiff_by_puuid.sort_values('riot_id')
    avg_xpdiff_by_puuid['role'] = roles
    avg_xpdiff_by_puuid.set_index('role', inplace = True)
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

    col_tab1,col_tab2 = st.columns([2,2])
    # Rentability section
    with col_tab1:
        
        st.markdown('<h2 class="title">Rentability</h2>', unsafe_allow_html=True)
        st.write('Rentability for each player (Gold/Dmg per minute)')
        st.write(df_dmg_gold_filtered[['riot_id', 'Dmg/Gold Ratio']])
    
    # XP Diff 
    with col_tab2:
        
        st.markdown('<h2 class="title">XP Diff </h2>', unsafe_allow_html=True)
        st.write('XP Management in lanes (average at 5/10/15 minutes)')   
        st.write(avg_xpdiff_by_puuid)


 
    #st.write(df)

