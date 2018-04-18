import React, { Component } from 'react';
import './App.css';

import Map from './Map';
import BarChart from './BarChart';
import Button from './Button';
import Menu from './Menu';
import results from './data/Milano/results.js';
import resultsTorino from './data/Torino/results.js';
import istruzioneTorino from './data/Torino/istruzione.js';
import geojsonMilano from './data/Milano/NILZone.EPSG4326.js';
import geojsonTorino from './data/Torino/0_geo_zone_circoscrizioni_wgs84.js';
import menu from './data/menu.js';
import { range } from 'd3-array';
import { scaleLinear } from 'd3-scale';

//set default city
var city = "Milano";

var colors = ['#FFFFDD',
              '#AAF191',
              '#80D385',
              '#61B385',
              '#3E9583',
              '#217681',
	      '#285285',
              '#1F2D86',
              '#000086'];
var geojson = getGeojson(city);

class App extends Component {
    colors = {};

    constructor(props) {
	super(props);

	this.layers = this.getAllLayers(menu);
	this.cities = this.layers
	    .map(i => i.city)
	    .filter(onlyUnique);
	this.cityLayers = this.layers
            .filter(i => i.city === city);
	this.setDefaultSource(city);
	this.setDefaultLayer(city);
	
	this.state = {
	    city: city,
	    layer: this.defaultLayer,
	    hover: "none",
	    clicked: "none"
	};
	
        this.center = this.defaultSource.center;
        this.zoom = this.defaultSource.zoom;
        this.joinField = this.defaultSource.joinField;
	
	this.setFeatures(this.state.layer);
	this.setColors(this.state.layer);
	
	this.changeCity = this.changeCity.bind(this);
	this.changeLayer = this.changeLayer.bind(this);
	this.onClickMap = this.onClickMap.bind(this);
	this.onHoverBarChart = this.onHoverBarChart.bind(this);
	this.onHoverMap = this.onHoverMap.bind(this);
    };

    getAllLayers(menu) {
	var layers = [];
	menu.forEach(m => {
            if (m.indicators !== undefined) {
                layers = layers.concat(m.indicators.map(c => {
                    if (m.type === "source") {
                        return {
                            id: c.id,
                            label: c.label,
                            category: c.category,
                            sourceId: m.id,
                            sourceUrl: m.url,
                            city: m.city,
			    dataSource : m.dataSource,
                            default: c.default
                        };
                    } else if (m.type === "layer") {
                        var sourceUrl = menu.filter(d => d.id === m.sourceId)[0].url;
                        return {
                            id: c.id,
                            label: c.label,
                            category: c.category,
                            layerId: m.id,
                            layerUrl: m.url,
                            sourceId : m.sourceId,
			    dataSource : m.dataSource,
                            sourceUrl: sourceUrl,
                            city: m.city,
                            default: c.default
                        };
                    }
                }))
            }
        });
	return layers;
    };
    
    setDefaultLayer(city) {
        this.defaultLayer = this.cityLayers
            .filter(l => (l.default !== undefined && l.default))[0];
        if (this.defaultLayer === undefined) {
            console.log("Error: city " + city + " doesn't have a default layer, check the menu file and add property default to one of the indicators");
        }
    };

    setDefaultSource(city) {
	this.defaultSource = menu
            .filter(m => m.city === city)
            .filter(m => m.default !== undefined && m.default)[0];
        if (this.defaultSource === undefined) {
            console.log("Error: city " + city + " doesn't have a default source, check the menu file and add property default to one of the sources for " + city);
        }
    };
    
    getMenu() {
	var layers = this.cityLayers;
	var categories = layers.map(i => i.category)
            .filter(onlyUnique)
            .map(c => {
		var subcategories = layers.filter(i => i.category === c);
		return { category: c, subcategories: subcategories };
            });
	return categories;
    };

    onClickMap(d) {
	this.setState({ clicked: d.properties[this.joinField] });
    };
    
    onHoverBarChart(d) {
	this.setState({ hover: d[0] });
    };

    onHoverMap(d) {
	this.setState({ hover: d.properties[this.joinField] });
    };

    setColors(l) {
	var values = this.features.map((d) => d.properties[l.id]);
	values = sample(values, colors.length);
        this.colors.stops = values.map((d, i) => [values[i], colors[i]]);
        this.colors.scale = scaleLinear().domain(values).range(colors);
        this.colors.highlight = "black";
    };
    
    setFeatures(l) {
	this.features = geojson.features;
	var myLayer = this.cityLayers.filter(i => i.id === l.id)[0];
	if (myLayer.layerUrl !== undefined) {
	    //download data from layerUrl
	    var data = resultsJson(this.state.city, myLayer.layerId);
	    
	    var quartieri = data.map(d => d[this.joinField]);
	    //console.log(quartieri)
	    //console.log(this.features.map(d => d.properties[this.joinField]))
	    this.features.forEach(d => {
		
		var index = quartieri.indexOf(d.properties[this.joinField]);
		d.properties[l.id] = data[index][l.id];
	    });
	}
	
	this.features = this.features
	    .sort((a, b) => b.properties[l.id] - a.properties[l.id]);
   };

    changeCity(d, label) {
        if (this.state.city !== label) {
            this.setState({ city: label });
        }
    };

    changeLayer(d) {
        if (this.state.layer.id !== d.id) {
            this.setState({ layer: d });
        }
    };
    
    componentWillUpdate(nextProps, nextState) {
	if (nextState.city !== this.state.city) {
	    geojson = getGeojson(nextState.city);

	    this.cityLayers = this.layers
		.filter(i => i.city === nextState.city);
	    
	    this.setDefaultSource(nextState.city);
            this.center = this.defaultSource.center;
            this.zoom = this.defaultSource.zoom;
	    this.joinField = this.defaultSource.joinField;
	    
	    this.setDefaultLayer(nextState.city);
	    this.setState({ layer: this.defaultLayer });
	} else if (nextState.layer.id !== this.state.layer.id) {
	    this.setFeatures(nextState.layer);
	    this.setColors(nextState.layer);
	    this.setState({ clicked: "none" });
	}
    };
        
    render() {
	var self = this;
	return (
	   
           <div className="App">
		<div className="App-header">
		    <div style={{ display: "flex", justifyContent: "space-between" }}>
		        <Menu
	                    menu={this.getMenu()}
	                    handleClick={this.changeLayer}/> 
		        <h2>Mappa dei quartieri di {this.state.city}</h2>
                
		        <div>
		            {this.cities.map(city =>
				      <Button
				       handleClick={this.changeCity}
				       label={city}/>)}
		        </div>
		    </div>
		</div>
		<div style={{ display: "flex" }}>
		            
		            <Map
	                        clicked={this.state.clicked}
	                        hoverElement={this.state.hover}
	                        onHover={this.onHoverMap}
	                        onClick={this.onClickMap}
	                        options={{
		                    city: this.state.city,
				    center: this.center,
				    zoom: this.zoom
				}} 
	                        data={{
		                    type: "FeatureCollection",
				    features: this.features
				}}
	                        layer={{
		                    id: this.state.layer.id,
				    colors: this.colors
				}}
	                        joinField={this.joinField}
		            />
		        
	                <div style={{ width: "30vw" }}>
	                     <BarChart
	                        clicked={this.state.clicked}    
	                        hoverElement={this.state.hover}
	                        onHover={this.onHoverBarChart}
	                        data={{
		                    city: this.state.city,
		                    label: this.state.layer.label,
				    dataSource: this.state.layer.dataSource,
				    headers: [this.joinField, this.state.layer.id],
		                    values: this.features.map(d => [d.properties[self.joinField], d.properties[self.state.layer.id]]),
				    colors: this.colors
				}}
		            />   
	                </div>
		</div>	
            </div>
	)
    };
}

function getGeojson(city) {
    var toreturn;
    if (city === "Milano") {
        toreturn = geojsonMilano;
    } else if (city === "Torino") {
	toreturn = geojsonTorino;
    }
    return toreturn;
};

function resultsJson(city, id) {
    var toreturn;
    if (city === "Milano") 
	toreturn = results;
    
    if (city === "Torino" && id === "istatTorino")
	toreturn = resultsTorino;
    if (city === "Torino" && id === "istruzioneTorino")
	toreturn = istruzioneTorino;
    
    return toreturn;
};

function onlyUnique(value, index, self) {
    return self.indexOf(value) === index;
};

function sample(values, C) {
    var min = Math.min(...values),
        max = Math.max(...values);
    return [...Array(C).keys()]
        .map((d) => d * (max - min) / C  + min);
};

export default App;

