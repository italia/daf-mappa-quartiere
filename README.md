# Mappa Quartiere

A data application consisting of visualizations and numerical analyses to monitor the liveability of Italian cities neighbourhoods.
We aim to measure the availability of some publicly-organised services in the different areas of each cities, as well as to evaluate the difference in vitality between them. The output metrics are built on open data collected from various sources (ISTAT, Ministries of Education, Health and Culture, local municipalities).

Currently under development.

## Files
* `/data` contains the source files. In particular, _processed_ and _output_ contain the inputs and the outputs from the model processing, respectively 
* `/notebooks` has the Jupyter notebooks that run the various steps of the data pipeline
* `/src/models` has the python libraries to obtain the neighbourhood-level KPI
* `/src/visualization` has the js libraries of the front-end visualization
* `/src/testing` has the testing modules for the codebase and the processed data

Production files are stored in an external repo as a temporary replacement for an API data source.
The server repo can be found [here](https://github.com/esterpantaleo/daf-server).

## Use

### Visualization
To see the visualization first follow instructions in [the server repo](https://github.com/esterpantaleo/daf-server/README.md) (this will start a server at `localhost:4000`), then cd into src/visualization/ and then run `npm i` and `npm start`. You should see a dashboard at `localhost:3000`.

### Running underlying model
Main notebook is [CityServicesModel](https://github.com/italia/daf-mappa-quartiere/blob/master/notebooks/CityServicesModel.ipynb): it can be used to reproduce all the computational steps for the city selected at the beginning.

### Running tests
Code tests are implemented via the standard `unittest` framework and stored in the _src/testing_ folder.

### Additional info
The files and folder structure is designed to follow the specs at:
https://github.com/drivendata/cookiecutter-data-science
Python enviroment specs can be found in `requirements.txt`.
The visualization uses React and has been built with [Create React App](https://github.com/facebookincubator/create-react-app).
