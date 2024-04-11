import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
import json
import base64
import matplotlib.pyplot as plt 
import numpy as np 
st.set_page_config(layout="wide")   
pd.set_option("styler.render.max_elements", 484800)

# Stylish header
st.markdown(
    """
    <h2 style='text-align: center; color: #f63366;'>Nexus Tour Reporting</h2>
    <h4 style='text-align: center; color: #ffffff;'>LIGHT THEME RECOMMENDED</h4>
    <hr style='margin-bottom: 20px;'>
    """,
    unsafe_allow_html=True
)

def path_to_image_html(path): #crédit mascode 
    '''
     This function essentially convert the image url to 
     '<img src="'+ path + '"/>' format. And one can put any
     formatting adjustments to control the height, aspect ratio, size etc.
     within as in the below example. 
    '''

    return '<img src="'+ path + '" style="max-height:50px;"/>'

def plot_positions_on_map(map_image, positions):

    # Plot the map image
    fig, ax = plt.subplots()
    ax.imshow(map_image)

    # Extract x, y positions from the positions dictionary
    for puuid, pos_list in positions.items():
        x_values = [pos['x'] for pos in pos_list]
        y_values = [pos['y'] for pos in pos_list]

        # Plot the positions on the map
        ax.scatter(x_values, y_values, label=puuid)



    return fig

df = pd.read_csv("nexus_tour/csv/nexustour_etape1_raw_data.csv")
df_2 = pd.read_csv("nexus_tour/csv/nexustour_etape2_raw_data.csv")

# STEP 1 DATA 
with open('nexus_tour/json/dict_position_lvl1_red_etape1.json', "r") as file:
    dict_position_red = json.load(file)
with open('nexus_tour/json/dict_position_lvl1_blue_etape1.json', "r") as file:
    dict_position_blue = json.load(file)
    
df_dmg_gold = pd.read_csv('nexus_tour/csv/gold_dmg_ratio_etape1.csv')
df_dmg_gold.rename(columns={'avg':'Dmg/Gold Ratio'}, inplace = True)

# STEP 2 DATA
with open('nexus_tour/json/dict_position_lvl1_red_etape2.json', "r") as file:
    dict_position_red_2 = json.load(file)
with open('nexus_tour/json/dict_position_lvl1_blue_etape2.json', "r") as file:
    dict_position_blue_2 = json.load(file)
    
df_dmg_gold_2 = pd.read_csv('nexus_tour/csv/gold_dmg_ratio_etape1.csv')
df_dmg_gold_2.rename(columns={'avg':'Dmg/Gold Ratio'}, inplace = True)

page = st.sidebar.radio("Navigation", ("Nexus Tour Reporting","Team Focus","Player focus"))

if page == "Player focus":
    
    # Filter options
    riot_ids = df['riot_id'].unique()
    sides = ['red', 'blue']
    # Sidebar filters 
    selected_riot_id = st.sidebar.selectbox("Select Riot ID", riot_ids)
    selected_side = st.sidebar.multiselect("Select Side", sides)
    # filters
    puuid = df[df['riot_id'] == selected_riot_id]['puuid'].unique()
    filtered_df = df[df['riot_id'] == selected_riot_id]
    if selected_side:
        filtered_df = filtered_df[filtered_df['side'].isin(selected_side)]
    
    # Nickname displaying
    st.write(f"# <div style='text-align: center;'>{selected_riot_id}</div>", unsafe_allow_html=True)

    # get Xpdiff for the select player
    avg_xpdiff = filtered_df.groupby('champion').agg({'xpdiff_at5': 'mean', 'xpdiff_at10': 'mean', 'xpdiff_at15': 'mean'}).reset_index()

    # Count nb of games and merge it 
    nb_game = filtered_df.groupby('champion').size().reset_index(name='games')
    avg_xpdiff_by_champion = pd.merge(avg_xpdiff, nb_game, on='champion')
    avg_xpdiff_by_champion = avg_xpdiff_by_champion.round(1)

    
    # Compute win rates
    win_rates = filtered_df.groupby('champion')['win'].agg(['mean', 'size'])  # Aggregate mean and count
    win_rates.columns = ['win_rate', 'games']
    win_rates['win_rate'] = (win_rates['win_rate']*100).round(1)
    win_rates.sort_values(by = 'games', ascending = False, inplace = True)
    win_rates = win_rates.reset_index(drop = False)
    
    # get image links for each champion
    win_rates = win_rates.reset_index(drop = False)
    df_player = pd.merge(win_rates[['champion', 'win_rate']], avg_xpdiff_by_champion, on='champion')
    df_player['Champ'] = "https://ddragon.leagueoflegends.com/cdn/14.5.1/img/champion/" + win_rates['champion'] + ".png"
    df_player.drop(columns = ['champion'], inplace = True )     
    columns = ['Champ'] + [col for col in df_player.columns if col != 'Champ']
    df_player = df_player[columns]  
    df_player = df_player.style.format({"Champ":path_to_image_html, "win_rate": lambda x: f"{x:.1f}", "xpdiff_at5": lambda x: f"{x:.1f}", "xpdiff_at10": lambda x: f"{x:.1f}", "xpdiff_at15": lambda x: f"{x:.1f}" })
    df_player = df_player.hide(axis = 'index')  
    df_player = df_player.to_html(index = False)

    st.subheader('Player Focus on XP diff and W/R per champ')
    st.markdown(df_player, unsafe_allow_html= True)
    st.write(filtered_df['team'])
  

elif page == "Nexus Tour Reporting":
   
    #choose steps 
    available_options = ['Step 1', 'Step 2 (GA)', 'All']
    selected_option = st.sidebar.selectbox("Select Option", available_options)

    if selected_option == 'Step 1':
        df = df
    elif selected_option == 'Step 2 (GA)':
        df = df_2
    else:  # selected_option == 'Both'
        df = pd.concat([df, df_2], ignore_index=True)


    # Create tabs for each role
    roles = ['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY']
    
    # display each role winrate on a column 
    col1, col2,col3,col4,col5 = st.columns([7,7,7,7,7])
    columns = [col1,col2,col3,col4,col5]
    for role,col in zip(roles,columns):
        
        #get the winrate for each player according to his role 
        role_df = df[(df['team_position'] == role)]
        win_rates = role_df.groupby('champion')['win'].agg(['mean', 'size'])  # Aggregate mean and count
        win_rates.columns = ['W/R', 'games']
        win_rates['W/R'] = (win_rates['W/R'] * 100).round(1)
        win_rates = win_rates.sort_values(by='games', ascending = False)
        
        # display images 
        win_rates = win_rates.reset_index(drop = False)
        win_rates['Champ'] = "https://ddragon.leagueoflegends.com/cdn/14.5.1/img/champion/" + win_rates['champion'] + ".png"
        win_rates.drop(columns=['champion'], inplace = True)
        columns = ['Champ'] + [col for col in win_rates.columns if col != 'Champ']
        win_rates = win_rates[columns]   
        win_rates = win_rates.style.format({"Champ":path_to_image_html, "W/R": lambda x: f"{x:.1f}"})
        win_rates = win_rates.hide(axis = "index")
        win_rates = win_rates.to_html(escape = False)
   
        with col:
           st.write(f"### {role} ")
           st.markdown(win_rates, unsafe_allow_html= True)

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
    if not selected_side :
        selected_side = sides        
    if len(filtered_df['riot_id'])>5:
        filtered_df = filtered_df[filtered_df['riot_id'] != 'DÉMON LIBÉRÉ'].reset_index(drop = True)
    # get list of nicknames & puuid of the selected ppl
    list_puuid = filtered_df['puuid'].unique().tolist()



    #get the right position points for lvl 1 according to side 
    if selected_side[0] == 'blue' and len(selected_side) == 1:
        
        filtered_positions = {puuid: dict_position_blue[puuid] for puuid in list_puuid}
        points_data = []
        for key, value in filtered_positions.items():
            points_data.extend(value)

    elif selected_side[0] == 'red' and len(selected_side) == 1: 
        filtered_positions = {puuid: dict_position_red[puuid] for puuid in list_puuid}
        points_data = []
        for key, value in filtered_positions.items():
            points_data.extend(value)

    else : 

        filtered_positions_blue = {puuid: dict_position_blue[puuid] for puuid in list_puuid}
        filtered_positions_red = {puuid: dict_position_red[puuid] for puuid in list_puuid}
        points_data = []
        for (key, value),(key_2,value2) in zip(filtered_positions_blue.items(),filtered_positions_red.items()):
            points_data.extend(value)
            points_data.extend(value2)
        


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
    
    
    #display
    st.markdown('<h2 class="title">Pick History</h2>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([5, 5, 5, 5, 5])
    columns = [col1, col2, col3, col4, col5]
    col_nb = 0

    for role, col in zip(roles, columns):
        
        #get the  winrate for each role
        role_df = filtered_df[filtered_df['team_position'] == role]
        win_rates = role_df.groupby('champion')['win'].agg(['mean', 'size'])  # Aggregate mean and count
        win_rates.columns = ['W/R', 'games']
        win_rates['W/R'] = (win_rates['W/R'] * 100).round(2)
        win_rates = win_rates.sort_values(by='games', ascending=False)
        
        #display images
        win_rates = win_rates.reset_index(drop = False)
        win_rates['Champ'] = "https://ddragon.leagueoflegends.com/cdn/14.5.1/img/champion/" + win_rates['champion'] + ".png"
        win_rates.drop(columns=['champion'], inplace = True)
        columns = ['Champ'] + [col for col in win_rates.columns if col != 'Champ']
        win_rates = win_rates[columns]   
        win_rates = win_rates.style.format({"Champ":path_to_image_html, "W/R": lambda x: f"{x:.1f}"})
        win_rates = win_rates.hide(axis = "index")
        win_rates = win_rates.to_html(escape = False)
        
        with col:
            st.write(f"##### {role[0] + role[1:].lower()}: {list_nicknames[col_nb]}")
            st.markdown(win_rates, unsafe_allow_html= True)
            col_nb += 1
    st.markdown('</div>', unsafe_allow_html=True)


    col_tab1,col_tab2 = st.columns([2,2])
    
   
    with col_tab2:

         # Rentability section
        st.markdown('<h2 class="title">Rentability</h2>', unsafe_allow_html=True)
        st.write('Rentability for each player (Gold/Dmg per minute)')
        st.write(df_dmg_gold_filtered[['riot_id', 'Dmg/Gold Ratio']])
    
    
    with col_tab1:  

        # XP Diff 
        st.markdown('<h2 class="title">XP Diff </h2>', unsafe_allow_html=True)
        st.write('XP Management in lanes (average at 5/10/15 minutes)')   
        st.write(avg_xpdiff_by_puuid)


        # MAP POSITION
        map_image_path = 'nexus_tour/Image/summoners_rift.png'
        map_image = plt.imread(map_image_path)

        # Plot the image
        fig, ax = plt.subplots(figsize = (5,5))
        ax.imshow(map_image, extent=[0, 15000, 0, 15000])

        # Plot the points on the image
        for point in points_data:
            ax.scatter(point['x'], point['y'], color='red')

        # Set axis limits to match image dimensions
        ax.set_xlim(0, 15000)
        ax.set_ylim(0, 15000)
        ax.axis('off')

        # Show plot
        st.subheader('LVL 1 MAP (position at 1 min)')
        st.write("PICK ONLY ONE SIDE TO BE EFFICIENT - soon points will be coloured by the side ")
        plot_column, _ = st.columns([1,1])  # Adjust the width ratio as needed
        with plot_column:
            st.pyplot(fig)



  

 


