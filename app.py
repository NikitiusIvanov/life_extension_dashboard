import os
import json
import numpy as np
import pandas as pd
import plotly.express as px

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

######################################################################
# Downoload data
# load life expectancy table country, age, sex specific with estimated 
# life expectancy exstension calculated by manageable risk factors mortality excluded
le_calculated_risk_excluded_all_countries_df = pd.read_csv(
    os.path.join(
        'data',
        'risk_excluded_le.csv'
    )
)

risk_impact = le_calculated_risk_excluded_all_countries_df[['location_id', 'age', 'sex_id', 'rei_id', 'E_x_diff']]
life_expectancy = le_calculated_risk_excluded_all_countries_df[['location_id', 'age', 'sex_id', 'E_x_val']]

# load risk manageable ierarchy
risks_parents_names_manageable = pd.read_csv(
    os.path.join('data', 'risks_parents_names_manageable.csv')
)

#load risk factors names manageable
risks_names_manageable = pd.read_csv(
    os.path.join('data', 'risks_names_manageable.csv')
)

# load risk_ierarchy and names to id mapping
rei_ierarchy = pd.read_csv(
    os.path.join('data','rei_ierarchy.csv')
)

rei_ierarchy_3_level_manageable = pd.read_csv(
    os.path.join(
        'data',
        'rei_ierarchy_3_level_manageable.csv'
    )
)

# load mapping countries ids names and centroid coordinates
gbd_country_name_id_iso_centroid = pd.read_csv(
    os.path.join('data', 'gbd_country_name_id_iso_centroid.csv'),
)

# load code book with mappings names and ids entities from gbd research
code_book = pd.read_csv(
    os.path.join('data','code_book.csv')
).iloc[1:, 1:]

# load risk names to color map
rei_color_map = {
    k:v for k,v in pd.read_csv(
        os.path.join('data', 'rei_color_map.csv')
    ).values
}
# set mapping risk manageable parent to list of their childrens
risks_parents_names_manageable = {
    x: [
        y for y in 
        risks_parents_names_manageable
        .copy()
        .query('rei_parent_name == @x')
        .rei_name.unique()
    ]
    for x in 
    risks_parents_names_manageable
    .rei_parent_name
    .unique()
}

# transform risk factors names to list
risks_names_manageable = list(np.concatenate(risks_names_manageable.values))

# set mapping risk factors ids to their parents
risk_id_to_parent_id = {
    int(k):int(v)
    for k,v in rei_ierarchy[['rei_id','parent_id']].values
}

# set mapping sex names to id
sex_name_to_id = {
    key: int(value) 
    for key, value in code_book[['sex_label', 'sex_id']].dropna().values[1:]
}

sex_id_to_name = {k: v for v, k in sex_name_to_id.items()}

# set mapping risk factors names to id
risks_name_to_id = {
    key: int(value) 
    for key, value in code_book[['rei_name', 'rei_id']].dropna().values
}

risks_id_to_name = {k: v for v, k in risks_name_to_id.items()}

# set mapping country name to gbd id
location_name_to_id = {
    key: int(value) 
    for key, value in 
    gbd_country_name_id_iso_centroid[['location_name', 'location_id']].values
}

location_id_to_name = {k: v for v, k in location_name_to_id.items()}

# set mapping countries id to iso countries codes 
gbd_id_to_iso_code_map = {
    int(k): v for k,v in 
    gbd_country_name_id_iso_centroid[['location_id', 'iso_code']].values
}

# set mapping country id to longitude and latitude of their centroids 
gbd_country_id_to_centroid_map = {
    int(x[0]): [x[1], x[2]]
    for x in 
    gbd_country_name_id_iso_centroid
    [['location_id', 'latitude', 'longitude']]
    .values
}

# set additional colors
color_mapping = {
    'Default life expectancy': {
        'Male': 'rgba(89, 52, 235, 0.6)',
        'Female': 'rgba(235, 52, 155, 0.6)'
    },
    'Estimated life extension': {
        'Male': 'rgba(10, 38, 247, 0.9)',
        'Female': 'rgba(255, 15, 150, 0.9)'
    }
}

def prepare_data(
    location_name: str,
    age: int,
    sex_name: int,
    risk_factors_names: list,
    risks_parents_names_manageable: dict,
    risk_impact: pd.DataFrame,
    life_expectancy: pd.DataFrame,
    risk_id_to_parent_id: dict,
    location_name_to_id: dict,
    sex_name_to_id: dict,
    risks_name_to_id: dict,
    gbd_id_to_iso_code_map: dict,
    is_dietary_risks_groupped: bool=True,
    round_n_decimals: int=2,
) -> pd.DataFrame:

    ################################################
    # get risk names from parents
    risk_factors_names_source = risks_names_manageable.copy()
    risk_factors_names = np.concatenate([
        risks_parents_names_manageable[x]
        if x in risks_parents_names_manageable.keys()
        else [x]
        for x in risk_factors_names
    ])

    # get ids from names
    location_id = location_name_to_id[location_name]

    risk_factors_id = [risks_name_to_id[x] for x in risk_factors_names]

    sex_id = sex_name_to_id[sex_name]

    ################################################
    # filtering data by setted criteries
    risk_impact_filtered = risk_impact.query(
        f'location_id == {location_id}'
        ' and rei_id in @risk_factors_id'
    )

    life_expectancy_filtered = life_expectancy.query(
        f'location_id == {location_id}'
        f' and age == {age}'
    )[['sex_id', 'E_x_val']]

    risk_impact_filtered = (
        risk_impact_filtered
        .assign(rei_parent_id = lambda x: x.rei_id.map(risk_id_to_parent_id))
    )

    risk_impact_filtered['rei_name'] = (
        risk_impact_filtered.copy()['rei_id']
        .map({k:v for v,k in risks_name_to_id.items()})
    )

    risk_impact_filtered['rei_parent_name'] = (
        risk_impact_filtered.copy()['rei_parent_id']
        .map({k:v for v,k in risks_name_to_id.items()})
    )

    risk_impact_filtered_cur_age = (
        risk_impact_filtered
        .query(f'age == {age}')
        .round(decimals=round_n_decimals)
    )

    if is_dietary_risks_groupped == True:
        groupped_dietary_risks = (
            risk_impact_filtered
            .query('rei_parent_name == "Dietary risks"')
            .groupby(by=['sex_id', 'age', 'rei_parent_name'])
            [['E_x_diff']]
            .sum()
            .reset_index()
        )

        groupped_dietary_risks.columns = ['sex_id', 'age', 'rei_name', 'E_x_diff']
        
        risk_impact_filtered.columns
        
        risk_impact_filtered_dietary_groupped = pd.concat(
            [
                risk_impact_filtered
                .query('rei_parent_name != "Dietary risks"')
                [['sex_id', 'age', 'rei_name', 'E_x_diff']],
                groupped_dietary_risks
            ], axis=0,
        ).sort_values(by=['sex_id', 'age', 'E_x_diff'], ascending=False)
        
        risk_impact_filtered_dietary_groupped_cur_age = (
            risk_impact_filtered_dietary_groupped
            .query(f'age == {age}')
        )
        
    else:
        risk_impact_filtered_dietary_groupped = risk_impact_filtered.copy()
        risk_impact_filtered_dietary_groupped_cur_age = risk_impact_filtered_cur_age.copy()

    risk_impact_filtered_dietary_groupped = (
        risk_impact_filtered_dietary_groupped
        .query('sex_id == @sex_id')
    )

    ################################################
    # create report with summary extension by sex
    report_male = pd.DataFrame(
        {
            'Default life expectancy': (
                life_expectancy_filtered
                .query(f'sex_id == {sex_name_to_id["Male"]}')
                [['E_x_val']]
                .values[0]
                +
                age
            ),
            'Estimated life extension': (
                risk_impact_filtered_dietary_groupped_cur_age
                .query(f'sex_id == {sex_name_to_id["Male"]}')
                [['E_x_diff']]
                .sum()
                .values[0]
            ),
        },
        index=['val']
    )

    report_male['Extended life expectancy'] = (
        report_male['Default life expectancy']
        +
        report_male['Estimated life extension']
    )

    report_female = pd.DataFrame(
        {
            'Default life expectancy': (
                life_expectancy_filtered
                .query(f'sex_id == {sex_name_to_id["Female"]}')
                [['E_x_val']]
                .values[0]
                +
                age
            ),
            'Estimated life extension': (
                risk_impact_filtered_dietary_groupped_cur_age
                .query(f'sex_id == {sex_name_to_id["Female"]}')
                [['E_x_diff']]
                .sum()
                .values[0]
            ),
        },
        index=['val']
    )

    report_female['Extended life expectancy'] = (
        report_female['Default life expectancy']
        +
        report_female['Estimated life extension']
    )

    report_male['sex_name'] = 'Male'
    report_female['sex_name'] = 'Female'

    report = pd.concat([report_male, report_female])
    report.reset_index(inplace=True)
    report.set_index(['sex_name', 'index'], inplace=True)
    report = report.round(decimals=round_n_decimals).reset_index()

    ################################################
    # create data frames with estimated extension by countries
    risk_impact_by_countries = risk_impact.copy().query(
        'rei_id in @risk_factors_id'
        ' and age == @age'
        ' and sex_id == @sex_id'
    )

    risk_impact_by_countries['iso_code'] = (
        risk_impact_by_countries['location_id']
        .map(gbd_id_to_iso_code_map, na_action='ignore')
    )

    # sum by risk
    risk_impact_by_countries = (
        risk_impact_by_countries
        .groupby(by=['iso_code', 'location_id'])
        [['E_x_diff']].sum()
        .reset_index()
    )

    risk_impact_by_countries['location_name'] = (
        risk_impact_by_countries['location_id']
        .map({v:k for k,v in location_name_to_id.items()})
    )

    risk_impact_by_countries.columns = ['iso_code', 'location_id', 'Years', 'location_name']

    # sumarry impact for all selected risk factors
    risk_manageable_impact_summary = (
        risk_impact
        .query('rei_id in @risk_factors_id')
        .groupby(by=['location_id', 'age', 'sex_id'])
        [['E_x_diff']]
        .sum()
        .reset_index()
    )

    risk_impact_sum_for_all_countries = (
        risk_manageable_impact_summary
        .groupby(by=['age', 'sex_id'])
        [['E_x_diff']]
        .mean()
        .join(
            risk_manageable_impact_summary
            .groupby(by=['age', 'sex_id'])
            [['E_x_diff']]
            .quantile(q=0.05),
            rsuffix='_q05',
            how='left'
        )
        .join(
            risk_manageable_impact_summary
            .groupby(by=['age', 'sex_id'])
            [['E_x_diff']]
            .quantile(q=0.95),
            rsuffix='_q95',
            how='left'
        )
        .reset_index()
        .sort_values(by='age')
    )

    risk_impact_sum_for_all_countries['sex_name'] = (
        risk_impact_sum_for_all_countries['sex_id'].map({v: k for k, v in sex_name_to_id.items()})
    )

    ################################################
    # calculate total extension for title
    total_extension = round(
        risk_impact_filtered_cur_age
        .query(f'sex_id == @sex_id')
        .E_x_diff
        .sum(),
        ndigits=round_n_decimals
    )

    ################################################
    # create suptitles for plots

    life_expectancy_extension_male = round(
        report_male.loc["val", "Estimated life extension"],
        round_n_decimals
    )

    life_expectancy_extension_female = round(
        report_female.loc["val", "Estimated life extension"],
        round_n_decimals
    )

    life_expectancy_extension = {
        'Male': life_expectancy_extension_male,
        'Female': life_expectancy_extension_female
    }

    life_expectancy_extension_by_country_suptitle = (
        f' ###### Еxtension of life expectancy'
        f' by {len(gbd_id_to_iso_code_map.keys())} countries,'
        f' with excluding {len(risk_factors_names_source)} manageable risk factors'
        f' for {sex_name} aged {age} y.o.'
    )

    life_expectancy_extension_by_risk_suptitle = (
        f' ###### Еxtension of life expectancy,'
        f' by excluded {len(risk_factors_names_source)} manageable risk factors,'
        f' for {sex_name},'
        f' aged {age} y.o.,'
        f' in {location_name}'        
    )

    life_expectancy_extension_by_sex_suptitle = (
        f' ###### Extension of life expectancy by sex'
        f' for age {age} y.o.,'
        f' in {location_name}'        
    )

    life_expectancy_extension_by_age_suptitle = (
        f' ###### Extension of estimated life expectancy by age,'
        f' for {sex_name} in {location_name}'
    )

    return (
        total_extension,
        risk_impact_by_countries,
        risk_impact_sum_for_all_countries,
        risk_impact_filtered_cur_age,
        report,
        risk_impact_filtered_dietary_groupped,
        life_expectancy_extension_by_risk_suptitle,
        life_expectancy_extension_by_sex_suptitle,
        life_expectancy_extension_by_country_suptitle,
        life_expectancy_extension_by_age_suptitle,
    )


######################################################################
# Define plotters function
def life_expectancy_extension_by_country_plotter(
    risk_impact_by_countries: pd.DataFrame,
    gbd_country_id_to_centroid_map,
    location_name_to_id,
    location_name,
    total_extension,
) -> go.Figure:

    fig = px.choropleth(
        risk_impact_by_countries,
        locations="iso_code",
        color="Years",
        hover_name="location_name",
        title = "",
        color_continuous_scale=px.colors.sequential.dense
    )

    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='natural earth',
        ),
        height=400,
        margin = dict(t=0, l=0, r=0, b=0),
        coloraxis=dict(
            colorbar=dict(
                orientation='v',
                thickness=12,
                tickfont=dict(size=12),
                len=0.8,
                yanchor='middle',
            )
        ),
    )
    fig["layout"].pop("updatemenus")

    fig.add_trace(
        go.Scattergeo(
            lat=[gbd_country_id_to_centroid_map[
                location_name_to_id[location_name]
            ][0]],
            lon=[gbd_country_id_to_centroid_map[
                location_name_to_id[location_name]
            ][1]],
            mode='markers+text',
            marker=dict(
                size=7,
                color='white'
            ),
            text=[f'<b>{total_extension}<br>years</b>'],
            textfont=dict(
                color='black',
                size=15.02,
            ),
            textposition='top center',
            hoverinfo='skip',
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scattergeo(
            lat=[gbd_country_id_to_centroid_map[
                location_name_to_id[location_name]
            ][0]],
            lon=[
                    gbd_country_id_to_centroid_map
                    [
                        location_name_to_id
                        [
                            location_name
                        ]
                    ]
                    [1]
                ],
            mode='markers+text',
            marker=dict(
                size=6,
                color='rgb(250, 46, 35)'
            ),
            text=[f'<b>{total_extension}<br>years</b>'],
            textfont=dict(
                color='rgb(250, 46, 35)',
                size=15,
            ),
            textposition='top center',
            hoverinfo='skip',
            showlegend=False,
        )
    )

    return fig


def life_expectancy_extension_by_risk_plotter(
    risk_impact_filtered_dietary_groupped: pd.DataFrame,
    rei_color_map: dict,
    age: int,
) -> go.Figure:

    data_to_plot = (
        risk_impact_filtered_dietary_groupped
        .query('age == @age')
        [
            [
                'E_x_diff',
                'rei_name',
        ]
        ]
        .sort_values(by='E_x_diff', ascending=False)
        .round(2)
    )

    # Sample data for the pie chart
    total_sum = round(data_to_plot['E_x_diff'].sum(), 1)

    outer_labels = data_to_plot['rei_name']
    outer_values = data_to_plot['E_x_diff']
    outer_colors = [rei_color_map[x] for x in data_to_plot['rei_name']]

    # Create the pie chart trace
    outer_pie = go.Pie(
        labels=outer_labels,
        values=outer_values,
        textinfo='value',
        textfont=dict(size=15),
        hole=0.65,  # Set the size of the hole inside the pie chart (0.6 means 60% of the radius)
        marker=dict(colors=outer_colors),  # Set colors for each sector
        sort=False
    )

    # Calculate the center position for the text annotation
    center_x = 0.5
    center_y = 0.55


    fig = go.Figure(data=[outer_pie])

    # Set layout properties for the figure
    fig.update_layout(
        annotations=[
            dict(
                x=center_x,
                y=center_y,
                showarrow=False,
                text=f'<b>+{total_sum}</b>',  # Text to display in the center
                font=dict(size=35, color='black',),
            ),
            dict(
                x=center_x,
                y=center_y - 0.1,
                showarrow=False,
                text=f'<b>years</b>',  # Text to display in the center
                font=dict(size=20, color='black',),
            )

        ],
    )

    fig.update_layout(
        template='plotly_white',
        height=300,
        margin = dict(t=0, l=0, r=0, b=0),
        legend=dict(
            title="Excluded risk factors",
        ),
    )

    # Show the figure
    return fig


def life_expectancy_extension_by_sex_plotter(
    report: pd.DataFrame,
    age: int,
    color_mapping: dict,
    width: float=0.4
) -> go.Figure:

    x_data = {
        sex_name: {
            'Default life expectancy': report.loc[sex_name, 'Default life expectancy'],
            'Estimated life extension': report.loc[sex_name, 'Estimated life extension']
        }    for sex_name in ['Male', 'Female']
    }

    maximum_le = max(
        [
            report.loc[sex_name, 'Extended life expectancy']
            for sex_name in ['Male', 'Female']
        ]
    )
    
    #report = round(report.copy(), 1)

    fig = go.Figure()

    for sex_name in ['Female', 'Male']:

        percent_extension = round(
            100 * (
                report.loc[sex_name, 'Estimated life extension']
                /
                report.loc[sex_name, 'Default life expectancy']
            ),
            1
        )

        percent_default = 100 - percent_extension

        fig.add_trace(
            go.Bar(
                y=[x_data[sex_name]['Default life expectancy']],
                x=[sex_name],
                orientation='v',
                marker=dict(
                    color=color_mapping['Default life expectancy'][sex_name],
                    line=dict(width=1)
                ),
                text=(
                    f"{report.loc[sex_name, 'Default life expectancy']}"
                    f"<br>({percent_default} %)"
                ),
                textfont=dict(color='white', size=13),
                insidetextanchor='end',
                hovertemplate='Default life expectancy<br> is: %{y} years',
                name=f'{sex_name} default life expectancy',
                width=width,
                legendgroup=sex_name,
                showlegend=True
            )
        )

        fig.add_trace(
            go.Bar(
                y=[x_data[sex_name]['Estimated life extension']],
                x=[sex_name],
                orientation='v',
                marker=dict(
                    color=color_mapping['Estimated life extension'][sex_name],
                    line=dict(width=1)
                ),
                text=(
                    f"{report.loc[sex_name, 'Estimated life extension']}"
                    f"<br>({percent_extension} %)"
                ),
                textfont=dict(color='white', size=13),
                textposition = "inside",
                insidetextanchor='middle',
                hovertemplate='Extension of life expectancy<br> is: %{y} years',
                name=f'{sex_name} extension',
                width=width,
                legendgroup=sex_name,
                showlegend=True
            )
        )

    fig.update_layout(
        template='plotly_white',
        height=400,
        yaxis=dict(
                range=(age, int(maximum_le * 1.05)),
                tickvals=list(range(age, int(maximum_le // 1 + 1), 5)),
                zeroline=False,
                showgrid=False,
                showline=False,
                domain=[0.15, 1],
                title='Life expectancy (Years)'
            ),
        xaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
        ),
        legend=dict(
            y=0.1,
            orientation="h"
        ),
        barmode='stack',
        bargap=0.001,
        showlegend=True,
        margin=dict(l=0, r=0, t=0, b=0),
    )

    return fig


def life_expectancy_extension_by_age_plotter(
    risk_impact_filtered_dietary_groupped: pd.DataFrame,
    rei_color_map: dict,
    age: int,
):

    age_arr = np.sort(risk_impact_filtered_dietary_groupped.age.unique())

    rei_sorted_by_val_sum = (
        risk_impact_filtered_dietary_groupped
        .groupby(by='rei_name')['E_x_diff']
        .sum()
        .sort_values(ascending=False)
        .index
    )
    
    fig = go.Figure()

    y = np.array([0 for _ in risk_impact_filtered_dietary_groupped.age.unique()], dtype='float64')

    for rei_name in rei_sorted_by_val_sum:

        cur_y = np.array(
            risk_impact_filtered_dietary_groupped
            .query(
                'rei_name == @rei_name'
            )
            .sort_values(by='age')
            ['E_x_diff'].values,
            dtype='float64'
        )

        y += cur_y

        fig.add_trace(
            go.Scatter(
                customdata=cur_y,
                x=age_arr,
                y=y,
                line=dict(
                    width=0.1,
                    color=rei_color_map[rei_name]
                ),
                fill='tonexty',
                hovertemplate =(
                    f'{rei_name},<br> '
                    'age: %{x:}, <br>extension: %{customdata:.2f}<extra></extra>'
                ),
                hoverinfo=None,
                name=rei_name
            )
        )
    if age is not None:
        cur_age_y = (
            risk_impact_filtered_dietary_groupped
            .query(
                'age == @age'
            )
            .set_index('rei_name').loc[rei_sorted_by_val_sum, :]
            ['E_x_diff']
            .cumsum()
        )

        fig.add_trace(
            go.Scatter(
                x=[age] * (len(cur_age_y.values) + 1),
                y=[0] + list(cur_age_y.values),
                mode='lines+markers',
                marker=dict(
                    color=[rei_color_map[rei_name] for rei_name in cur_age_y.index],
                    size=5,
                ),
                line=dict(
                    width=0.3,
                    color='red'
                ),
                hoverinfo='skip',
                showlegend=False,
            )
        )


    fig.update_layout(
        template='plotly_white',
        xaxis=dict(
            showgrid=False,
            showline=False,
            zeroline=False,
            title='Age(years)',
            tickvals=list(
                range(
                    risk_impact_filtered_dietary_groupped.age.min(),
                    risk_impact_filtered_dietary_groupped.age.max(),
                    5
                )
            )
        ),
        yaxis=dict(
            range=(0, risk_impact_filtered_dietary_groupped.groupby(by='age')['E_x_diff'].sum().max() * 1.05),
            showgrid=False,
            showline=False,
            zeroline=False,
            title='Life expectancy extension (years)',
        ),
        legend=dict(
            orientation="h",
            y=-0.1,
        ),
        margin=dict(l=0, r=0, t=0, b=0)  
    )

    return fig


######################################################################
# create the plotly dash application
app = Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
app.title = 'Life expectancy extension with risk factors excluding'
app._favicon = (os.path.join("assets", "favicon.ico"))

# setup layout
app.layout = dbc.Container(
    [
        dbc.Navbar(
            [
                dbc.Col(
                    [
                        html.H1(
                            children=(
                                'Estimate extension of life expectancy'
                                ' by excluding manageable risk factors'
                            ),
                            style={
                                "text-align": "center",
                                "align-items": "center",
                                "margin-top":"5px",
                                "padding": "5px",
                                "font-size": "20px"
                            }
                        )
                    ],
                    xs=12, sm=12, md=3, lg=3, xl=3,
                ),
                dbc.Col(
                    [
                        dbc.Label("Country", style={"margin-bottom": "0px", "font-size": "12px", "color": "gray"}),
                        dcc.Dropdown(
                            id="location_name",
                            options=list(location_name_to_id.keys()),
                            value='United States of America',
                            searchable=True,
                        ),
                    ],
                    xs=6, sm=6, md=2, lg=2, xl=2,
                    style={
                        "align-items": "center",
                        "padding": "5px",
                        "font-weight": "700"
                    }
                ),
                dbc.Col(
                    [
                        dbc.Label("Sex", style={"margin-bottom": "0px", "font-size": "12px", "color": "gray"}),
                        dcc.Dropdown(
                            id="sex_name",
                            options=['Male', 'Female'],
                            value='Male',
                        ),
                    ],
                    xs=3, sm=3, md=1, lg=1, xl=1,
                    style={
                        "padding": "5px",
                        "font-weight": "700"
                    }
                ),
                dbc.Col(
                    [
                        dbc.Label("Age y.o.", style={"margin-bottom": "0px", "font-size": "12px", "color": "gray"}),
                        dcc.Dropdown(
                            id="age",
                            options=list(range(0, 110, 1)),
                            value=42,
                        ),
                    ],
                    xs=3, sm=3, md=1, lg=1, xl=1,
                    style={
                        "padding": "5px",
                        "font-weight": "700"
                    }
                ),
                dbc.Col(
                    [
                        html.Details([
                            html.Summary(
                                'Check risk factors for exclude',
                                style={"margin-bottom": "0px", "margin-left": "10px",}
                            ),
                            # dbc.Label(
                            #     "Check risk factors for exclude",
                            #     style={"margin-left": "20px"},
                            # ),
                            dcc.Checklist(
                                id="risks_names_manageable",
                                options=risks_names_manageable,
                                inline=True,
                                value=risks_names_manageable,
                                inputStyle={"margin-left": "5px"},
                            ),
                        ])
                    ],
                    xs=12, sm=12, md=5, lg=5, xl=5,
                    style={
                        "padding": "5px",
                        "font-weight": "700",
                    }
                )
            ],
            color='#d3e7e8',
            fixed='top',
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Br(),
                        html.Br(),
                        html.Br(),
                        html.Br(),
                    ],
                    xs=12, sm=12, md=4, lg=4, xl=4,
                ),
                dbc.Col(
                    [
                        html.Br(),
                        html.Br(),
                        html.Br(),
                        html.Br(),
                    ],
                    xs=12, sm=12, md=4, lg=4, xl=4,
                ),
                dbc.Col(
                    [
                        html.Br(),
                    ],
                    xs=12, sm=12, md=4, lg=4, xl=4,
                )
            ]
        ),
        dbc.Row(
            [
                html.Details(
                    [
                        html.Summary(children='About data source and results'),
                        html.P(
                            children=(                                
                            [
                                'This dashboard visualize results of estimation change in '
                                ' life expectancy years in case exclusion from population deaths mortality attributed'
                                ' to the different manageable risk factors.'
                                ' Results contains sex-age related estimations for 26 risk factors in 204 countries.'
                                ' Sorce data for calculation was taken'
                                ' from ', dcc.Link(
                                    '2019 Global Burden of Disease (GBD) study.',
                                    href='https://vizhub.healthdata.org/gbd-results/',
                                ),
                                html.Br(),
                                html.Br(),
                                'Estimation process include:',
                                html.Li('Interpolation source data from 5-years group to 1 year group.'),
                                html.Li('Calculation of contribution each risk factor to the mortality using risk-attributed mortality.'),
                                html.Li('Calculation life tables with exclusion from mortality the contribution of each risk factor.'),
                                html.Li('Calculation difference in life expectancy with exclulsion risk-contributed mortality.'),
                                html.Br(),
                                ' All processes of data transformations published on github repository ', 
                                dcc.Link(
                                    'https://github.com/NikitiusIvanov/life_extension_dashboard_data_processing',
                                    href='https://github.com/NikitiusIvanov/life_extension_dashboard_data_processing',
                                ),
                                html.Br(),
                                'Source code of application also available on github:  ', 
                                dcc.Link(
                                    'https://github.com/NikitiusIvanov/life_extension_dashboard',
                                    href='https://github.com/NikitiusIvanov/life_extension_dashboard',
                                ),
                            ]
                            )
                        )
                    ]                    
                ),
                html.Br(),
                html.Details(
                    [
                        html.Summary(children='Manageable risk factors definitions'),
                        html.P(
                            children=(                                
                            [
                                html.B('Alcohol use.'),' We define current drinkers as individuals consuming at least one alcoholic beverage in the past year.',
                                html.Br(),
                                html.Br(),
                                html.B('Drug use.'),' Apart from drug use disorder estimates, '
                                'the drug use risk factor includes the risk of suicide in prevalent '
                                'cases of opioid, amphetamine,and cocaine use disorders, and the cumulative '
                                'incidence of blood-borne infections due to current and past injection drug use (IDU).',
                                html.Br(),
                                html.Br(),
                                html.B('Low physical activity.'), ' Low physical activity was measured in total metabolic equivalent (MET)'
                                ' minutes and was defined as average weekly physical activity (at work, home, transport related,'
                                ' and recreational) of less than 3000–4500 MET min per week.',
                                html.Br(),
                                html.Br(),
                                html.B('Unsafe sex.'), ' Unsafe sex is defined as the risk of disease due to sexual transmission. '
                                'Unsafe sex includes 100% of cervical cancer and STIs apartfrom those congenitally acquired'
                                ', and a fraction of HIV based on data reporting the proportion of HIV incidence through sexual transmission.',
                                html.Br(),
                                html.Br(),
                                html.B('High body-mass index.'), '  High BMI for adults (age ≥20 years) is defined as BMI greater than 20–25 kg/m². High '
                                'BMI for children (ages 1–19 years) is defined as being overweight or obese based on '
                                'International Obesity Task Force standards.',
                                html.Br(),
                                html.Br(),
                                html.B('High LDL cholesterol.'), ' We estimated blood concentration of LDL in units of mmol/L.'
                                ' We used a TMREL with a uniform distribution between 0·7 and 1·3 mmol/L.',
                                html.Br(),
                                html.Br(),
                                html.B('High fasting plasma glucose.'), ' High fasting plasma glucose is defined as serum'
                                ' fasting plasma glucose greater than 4·8–5·4 mmol/L.',
                                html.Br(),
                                html.Br(),
                                html.B('Smoking.'), ' Smoking is defined as current daily or occasional use of any smoked tobacco product.',
                                html.Br(),
                                html.Br(),
                                html.B('Secondhand smoke.'), ' This risk factor refers to current exposure to secondhand tobacco'
                                ' smoke at home, at work, or in other public places. Only non-daily smokers are'
                                ' considered to be exposed to secondhand smoke.',
                                html.Br(),
                                html.Br(),
                                html.B('Chewing tobacco.'), ' Current chewing tobacco use is defined as current daily or'
                                ' occasional use of chewing tobacco, including local products such as betel quid with tobacco.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet high in sodium.'), ' Diet high in sodium is defined as average 24-h urinary'
                                ' sodium excretion (in grams per day) greater than 3 g.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet high in processed meat.'), ' Diet high in processed meat is defined as any intake'
                                ' (in grams per day) of meat preserved by smoking, curing, salting, or addition of chemical preservatives.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in polyunsaturated fatty acids.'), ' Diet low in PUFAs is defined as average daily consumption'
                                ' (in percentage daily energy) of less than 7–9% total energy intake from PUFAs.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet high in red meat.'), ' Diet high in red meat is defined as any intake (in grams per day)'
                                ' of red meat including beef, pork, lamb, and goat but excluding poultry, fish, eggs, and all processed meats.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet high in trans fatty acids.'), ' Diet high in red meat is defined as any intake (in grams per day)'
                                ' of red meat including beef, pork, lamb, and goat but excluding poultry, fish, eggs, and all processed meats.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in vegetables.'), ' Diet low in vegetables is defined as average consumption (in grams per day)'
                                ' of less than 280–320 g of vegetables, including fresh, frozen, cooked, canned, or dried'
                                ' vegetables and excluding legumes, salted or pickled vegetables, juices, nuts and seeds,'
                                ' and starchy vegetables (eg, potatoes).',
                                html.Br(),
                                html.Br(),
                                html.B('Diet high in sugar-sweetened beverages.'), ' Diet high in sugar-sweetened beverages'
                                ' is defined as any intake (in grams per day) of beverages with at least 50 kcal'
                                ' per 226·8-g serving, including carbonated beverages, sodas, energy drinks,'
                                ' and fruit drinks, but excluding 100% fruit and vegetable juices.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in calcium.'), ' Diet low in calcium is defined as average daily consumption'
                                ' (in grams per day) of less than 1·06–1·10 g of calcium from all sources, including milk, yoghurt, and cheese.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in fiber.'), ' Diet low in fibre is defined as average daily consumption (in grams per day)'
                                ' of less than 21–22 g of fibre from all sources including fruits, vegetables, grains, legumes, and pulses.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in legumes.'), ' Diet low in legumes is defined as average daily consumption (in grams per day)'
                                ' of less than of 90–100 g of legumes and pulses, including fresh, frozen, cooked, canned, or dried legumes.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in nuts and seeds.'), ' Diet low in nuts and seeds is defined as average daily consumption'
                                ' (in grams per day) of less than 10–19 g of nuts and seeds, including tree nuts and seeds and peanuts.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in seafood omega-3 fatty acids.'), ' Diet low in omega-3 fatty acids is defined as average'
                                ' daily consumption (in milligrams per day) of less than 430–470 mg of eicosapentaenoic acid and docosahexaenoic acid.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in fruits.'), ' Diet low in fruit is defined as average daily consumption (in grams per day) of less'
                                ' than 310–340 g of fruit including fresh, frozen, cooked, canned, or dried fruit,'
                                ' excluding fruit juices and salted or pickled fruits.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in milk.'), ' Diet low in milk is defined as average daily consumption (in grams per day)'
                                ' of less than 360–500 g of milk including non-fat, lowfat, and full-fat milk and'
                                ' excluding soy milk and other plant derivatives.',
                                html.Br(),
                                html.Br(),
                                html.B('Diet low in whole grains.'), ' Diet low in whole grains is defined as average daily consumption '
                                '(in grams per day) of less than 140–160 g of whole grains (bran, germ, and endosperm'
                                ' in their natural proportion) from breakfast cereals, bread, rice, pasta, biscuits, '
                                'muffins, tortillas, pancakes, and other sources.',
                                html.Br(),
                            ]
                            )
                        )
                    ]                    
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [                           
                        html.Br(),
                        dcc.Markdown(
                            id='life_expectancy_extension_by_risk_suptitle',
                        ),
                        html.Br(),
                        dcc.Graph(
                            id="life_expectancy_extension_by_risk",
                            config={
                                 'displaylogo': False,
                                 'displayModeBar': False,
                            #     'editSelection': False,
                            #     'editable': False,
                            },
                            # animate=True,
                        ),
                    ],
                    xs=12, sm=12, md=5, lg=5, xl=5,
                ),
                dbc.Col(
                    [
                        html.Br(),
                        dcc.Markdown(
                            id='life_expectancy_extension_by_country_suptitle',
                        ),
                        dcc.Graph(
                            id="life_expectancy_extension_by_country",
                            config={
                                'displaylogo': False,
                                'displayModeBar': False,
                                'editSelection': False,
                                'editable': False,
                                'scrollZoom': False
                            },
                        )
                    ],
                    xs=12, sm=12, md=7, lg=7, xl=7,
                ),
            ]
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Markdown(
                            id='life_expectancy_extension_by_sex_suptitle',
                        ),
                        html.Br(),
                        dcc.Graph(
                            id="life_expectancy_extension_by_sex",
                                config={
                                    'displaylogo': False,
                                    'displayModeBar': False,
                                    'editSelection': False,
                                    'editable': False,
                                    'scrollZoom': False,
                                },
                                animate=True,
                        )
                    ],
                    xs=12, sm=12, md=5, lg=5, xl=5,
                ),
                dbc.Col(
                    [
                        dcc.Markdown(
                            id='life_expectancy_extension_by_age_suptitle',
                        ),
                        html.Br(),
                        dcc.Graph(
                            id="life_expectancy_extension_by_age",
                            config={
                                'displaylogo': False,
                                'displayModeBar': False,
                                'editSelection': False,
                                'editable': False,
                                'scrollZoom': False,
                            },
                            animate=True,
                        )
                    ],
                    xs=12, sm=12, md=7, lg=7, xl=7,
                )
            ]
        ),
        html.Br(),
        html.Br(),
        html.Div([dcc.Store(id='preprocessed_data')])
    ],
)

# setup the callback function for update plots
@app.callback(    
    Output(component_id='life_expectancy_extension_by_risk_suptitle', component_property='children'),
    Output(component_id='life_expectancy_extension_by_sex_suptitle', component_property='children'),
    Output(component_id='life_expectancy_extension_by_country_suptitle', component_property='children'),
    Output(component_id='life_expectancy_extension_by_age_suptitle', component_property='children'),
    Output(component_id='preprocessed_data', component_property='data'),
    Input(component_id='location_name', component_property='value'),
    Input(component_id='sex_name', component_property='value'),
    Input(component_id='age', component_property='value'),
    Input(component_id='risks_names_manageable', component_property='value'),
)
def update_data(
    location_name,
    sex_name,
    age,
    risks_names_manageable,
):

    (
        total_extension, # for title
        risk_impact_by_countries, # for plot distribution by country
        risk_impact_sum_for_all_countries, # for plot 95 conf interval by age
        risk_impact_filtered_cur_age, # for plot distribution by risk
        report, # for plot distribution by sex
        risk_impact_filtered_dietary_groupped, # for plot distribution by age
        life_expectancy_extension_by_risk_suptitle,
        life_expectancy_extension_by_sex_suptitle,
        life_expectancy_extension_by_country_suptitle,
        life_expectancy_extension_by_age_suptitle,
    ) = prepare_data(
        location_name=location_name,
        age=age,
        sex_name=sex_name,
        risk_factors_names=risks_names_manageable,
        risks_parents_names_manageable=risks_parents_names_manageable,
        risk_impact=risk_impact,
        life_expectancy=life_expectancy,
        risk_id_to_parent_id=risk_id_to_parent_id,
        location_name_to_id=location_name_to_id,
        sex_name_to_id=sex_name_to_id,
        risks_name_to_id=risks_name_to_id,
        gbd_id_to_iso_code_map=gbd_id_to_iso_code_map,
        is_dietary_risks_groupped=True,
        round_n_decimals=2,
    )

    preprocessed_data = {
        'risk_impact_by_countries': (
            risk_impact_by_countries
            .to_json(orient='split', date_format='iso')
        ),
        'risk_impact_sum_for_all_countries': (
            risk_impact_sum_for_all_countries
            .to_json(orient='split', date_format='iso')
        ),
        'risk_impact_filtered_cur_age': (
            risk_impact_filtered_cur_age
            .to_json(orient='split', date_format='iso')
        ),
        'report': (
            report
            .to_json(orient='split', date_format='iso')
        ),
        'risk_impact_filtered_dietary_groupped': (
            risk_impact_filtered_dietary_groupped
            .reset_index()
            .to_json(orient='split', date_format='iso')
        ),
    }

    return (
        life_expectancy_extension_by_risk_suptitle,
        life_expectancy_extension_by_sex_suptitle,
        life_expectancy_extension_by_country_suptitle,
        life_expectancy_extension_by_age_suptitle,
        json.dumps(preprocessed_data)
    )

@app.callback(
    Output(component_id='life_expectancy_extension_by_country', component_property='figure'),
    Input(component_id='preprocessed_data', component_property='data'),
    Input(component_id='location_name', component_property='value'),
    Input(component_id='sex_name', component_property='value'),
)

def update_life_expectancy_extension_by_country(
    preprocessed_data: json,
    location_name: str,
    sex_name: str,
):
    preprocessed_data = json.loads(preprocessed_data)

    risk_impact_by_countries = pd.read_json(
        preprocessed_data['risk_impact_by_countries'],
        orient='split'
    )

    report = pd.read_json(
        preprocessed_data['report'],
        orient='split'
    ).set_index(['sex_name', 'index'])

    total_extension = report.loc[sex_name].loc['val', 'Estimated life extension']

    life_expectancy_extension_by_country = life_expectancy_extension_by_country_plotter(
        risk_impact_by_countries=risk_impact_by_countries,
        gbd_country_id_to_centroid_map=gbd_country_id_to_centroid_map,
        location_name_to_id=location_name_to_id,
        location_name=location_name,
        total_extension=total_extension,
    )

    return life_expectancy_extension_by_country

#@app.callback(
#    Output(component_id='click_country_name', component_property='children'),
#    Input(component_id='life_expectancy_extension_by_country', component_property='clickData'))
#def update_click_country_name(clickData):
#    return clickData["points"][0]["hovertext"]


@app.callback(  
    Output(component_id='life_expectancy_extension_by_risk', component_property='figure'),
    Input(component_id='age', component_property='value'),
    Input(component_id='preprocessed_data', component_property='data'),
)
def update_life_expectancy_extension_by_risk(age, preprocessed_data):
    preprocessed_data = json.loads(preprocessed_data)
    
    risk_impact_filtered_dietary_groupped = pd.read_json(
        preprocessed_data['risk_impact_filtered_dietary_groupped'],
        orient='split'
    )

    life_expectancy_extension_by_risk = life_expectancy_extension_by_risk_plotter(
        risk_impact_filtered_dietary_groupped=risk_impact_filtered_dietary_groupped,
        rei_color_map=rei_color_map,
        age=age
    )

    return life_expectancy_extension_by_risk

@app.callback(  
    Output(component_id='life_expectancy_extension_by_sex', component_property='figure'), 
    Input(component_id='preprocessed_data', component_property='data'),
    Input(component_id='age', component_property='value'),
)
def update_life_expectancy_extension_by_sex(
    preprocessed_data,
    age,
):
    preprocessed_data = json.loads(preprocessed_data)    

    report = pd.read_json(
        preprocessed_data['report'],
        orient='split'
    )
    report = (
        report
        .drop('index', axis=1)
        .set_index('sex_name')
    )

    life_expectancy_extension_by_sex = life_expectancy_extension_by_sex_plotter(
        report,
        age,
        color_mapping,
    )

    return life_expectancy_extension_by_sex

@app.callback(   
    Output(component_id='life_expectancy_extension_by_age', component_property='figure'),
    Input(component_id='preprocessed_data', component_property='data'),
    Input(component_id='age', component_property='value'),
)
def update_life_expectancy_extension_by_age(
    preprocessed_data,
    age,
):
    preprocessed_data = json.loads(preprocessed_data)

    risk_impact_filtered_dietary_groupped = pd.read_json(
        preprocessed_data['risk_impact_filtered_dietary_groupped'],
        orient='split'
    )

    life_expectancy_extension_by_age = life_expectancy_extension_by_age_plotter(
        risk_impact_filtered_dietary_groupped=risk_impact_filtered_dietary_groupped,
        rei_color_map=rei_color_map,
        age=age,
    )

    return life_expectancy_extension_by_age

if __name__ == '__main__':
    app.run_server(debug=False, use_reloader=False, host='0.0.0.0', port=8080)
