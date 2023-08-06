# Interactive dashboard to visualize estimated life expectancy extension by excluding 26 manageable risk factors (for 204 countries, age and sex specific).
![Demo gif](https://github.com/NikitiusIvanov/life_extension_dashboard/blob/main/assets/gif_demo.gif)

Live demo serverless deployed on  Google cloud Run: https://life-extension-3oyids3kha-uc.a.run.app/

* All data kindly provided by Global Burden of Disease Study 2019 - https://vizhub.healthdata.org/gbd-results/
* Data preprocessing - https://github.com/NikitiusIvanov/life_extension_dashboard_data_processing

In this project we are using following stack:
  * Python as main programming language with libraries and frameworks:
    * Pandas, numpy - to data processing and calculation
    * Plotly Dash - to build web aplication with interactive visualizations
    * Docker - to application contenirization
    * Google cloud Run - to application deploy
