import React, { Component } from 'react';
import * as path from 'path';
import { range } from 'd3-array';
import { scaleLinear } from 'd3-scale';

import './App.css';
import Map from './Map';
import Button from './Button';
import Menu from './Menu';
//import results from './data/Milano/results.js';
import resultsTorino from './data/Torino/results.js';
import educazioneCulturaMilano from './data/Milano/Milano_EducazioneCultura.js';
import istruzioneTorino from './data/Torino/istruzione.js';


var menuUrl = "http://localhost:4000/menu.json";
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

class JsonMenu extends Component {
    
    constructor(props) {
	super(props);
	this.url = props;
    };
    
    getLayers(city) {
	if (city !== undefined) {
	    return this.layers.filter(i => i.city === city);
	}
	
	var self = this;

	var layers = [];
        self.data.forEach(m => {
            if (m.indicators === undefined)
                return {};
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
                }
                if (m.type === "layer") {
                    var sourceUrl = self.data.filter(d => d.id === m.sourceId)[0].url;
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
        });

	return layers;

    };

    getSources() {
	return this.data
	    .filter(m => m.type === "source");
    };

    getCities(){
        return this.layers
            .map(i => i.city)
            .filter(onlyUnique);
    };

    getCategories(city) {
	var cityLayers = this.layers.filter(i => i.city === city);
        var categories = cityLayers.map(i => i.category)
            .filter(onlyUnique)
            .map(c => {
                var subcategories = cityLayers.filter(i => i.category === c);
                return { category: c, subcategories: subcategories };
            });
        return categories;
    };

    getDefaultLayer(city) {
        return this.getLayers(city)
            .filter(l => (l.default !== undefined && l.default))[0];
    };

    getDefaultSource(city, sourceId) {
        return this.sources
            .filter(i => i.city === city)
            .filter(s => s.id === sourceId)[0];
    }

    setLayersSourcesCities() {
	this.layers = this.getLayers();
        this.sources = this.getSources();
        this.cities = this.getCities();

        this.sanityCheck();
    };
    
    sanityCheck() {
        if (this.cities.length === 0) {
            console.log("no cities in the menu");
        }

        var eachCityHasOneDefaultLayer = this.cities
            .map(city => this.layers
                 .filter(i => i.city === city)
                 .filter(l => (l.default !== undefined && l.default))
                 .length === 1)
        eachCityHasOneDefaultLayer
            .forEach((l, i) => {
                if (l === 0)
                    console.log("city " + this.cities(i) + " doesn't have one default layer");
            });

        var eachCityHasOneDefaultSource = this.cities
            .map(city => this.sources
                 .filter(i => i.city === city)
                 .filter(l => (l.default !== undefined && l.default))
                 .length === 1)
        eachCityHasOneDefaultSource
            .forEach((s, i) =>{
                if (s === 0)
                    console.log("city " + this.cities(i) + " doesn't have one default source");
            });
    };
    
    render() {
	return null;
    };
};

class App extends Component {
    colors = {};
    
    constructor(props) {
	super(props);

	this.state = {
            city: city,
	    source: "none",
            layer: "none",
	    menu: null,
	    features: null
        };
	
	this.changeCity = this.changeCity.bind(this);
        this.changeLayer = this.changeLayer.bind(this);

	var menu = new JsonMenu(menuUrl);
	fetch(menu.url)
	    .then(response => response.json())
            .then(json => menu.data = json)
            .then(() => {
                menu.setLayersSourcesCities();
		return menu;
            })
	    .then((jsonMenu) => {
		this.layers = jsonMenu.getLayers();
		
		var defaultLayer = jsonMenu.getDefaultLayer(this.state.city);
		var defaultSource = jsonMenu.getDefaultSource(this.state.city, defaultLayer.sourceId);
				
		fetch(defaultSource.url)
		    .then(response => response.json())
                    .then(jsonSource => {
			fetch(defaultLayer.layerUrl)
			    .then(response => response.json())
			    .then(jsonLayer => {
				var features = this.mergeFeatures(jsonSource.features, jsonLayer, defaultSource.joinField, defaultLayer.id);
			    	
				var values = features.map((d) => d.properties[defaultLayer.id]);
				this.setColors(values);
				
				this.setState({ menu: jsonMenu, layer: defaultLayer, source: defaultSource, features: features });
			    });
		    });	    
	    });
    };
    
    fetchSource(source) {
	return fetch(source.url)
	    .then(response => response.json())
	    .then(jsonSource => {
		this.setState({ features: jsonSource.features })
	    });
    };

    fetchLayer(layer, features) {
	return fetch(layer.layerUrl)
	    .then(response => response.json())
	    .then(jsonLayer => {
		var features = this.mergeFeatures(this.state.features, jsonLayer, this.state.source.joinField, layer.id);

		var values = features.map((d) => d.properties[layer.id]);
                this.setColors(values);

		this.setState({ layer: layer, features: features });
	    });
    };

    fetchSourceAndLayer(source, layer) {
	fetch(source.url)
            .then(response => response.json())
            .then(jsonSource => {
                fetch(layer.layerUrl)
                    .then(response => response.json())
                    .then(jsonLayer => {
                        var features = this.mergeFeatures(jsonSource.features, jsonLayer, source.joinField, layer.id);

                        var values = features.map((d) => d.properties[layer.id]);
                        this.setColors(values);
			
                        this.setState({ layer: layer, source: source, features: features });
                    });
            });
    };
    
    setColors(values) {
	values = sample(values, colors.length);
	
        this.colors.stops = values.map((d, i) => [values[i], colors[i]]);
        this.colors.scale = scaleLinear().domain(values).range(colors);
        this.colors.highlight = "black";
    };
    
    mergeFeatures(features, jsonLayer, joinField, layerField) {
	var quartieri = jsonLayer.map(d => d[joinField]);
	features.forEach(d => {
            var index = quartieri.indexOf(d.properties[joinField]);
            d.properties[layerField] = jsonLayer[index][layerField];
        });
        features = features
            .sort((a, b) => b.properties[layerField] - a.properties[layerField]);
	return features;
    };
    	
    fetchMenu(menu) {
        return fetch(menu.url)
	    .then(response => response.json())
            .then(json => menu.data = json)
            .then(() => {
		menu.setLayersSourcesCities()
		return menu;
            });
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

	    console.log("nextState.city !== this.state.city");
	    var defaultLayer = this.state.menu.getDefaultLayer(nextState.city);
	    var defaultSource = this.state.menu.getDefaultSource(nextState.city, defaultLayer.sourceId);
	    this.fetchSourceAndLayer(defaultSource, defaultLayer);

	} else if (nextState.layer !== this.state.layer) {
	    
	    console.log("nextState.layer !== this.state.layer")
	    this.fetchLayer(nextState.layer, this.state.features);
	    
	} 	
    };
        
    render() {
	if (this.state.layer === "none") {
	    console.log("this.state.layer === none");
	    return null;
	}
	
	var self = this;
	
	return (
           <div className="App">
		<div className="App-header">
		    <div style={{ display: "flex", justifyContent: "space-between" }}>
		        <Menu
	                    menu={this.state.menu.getCategories(this.state.city)}
	                    handleClick={this.changeLayer}/> 
		        <h2>Mappa dei quartieri di {this.state.city}</h2>
                
		        <div>
		            {this.state.menu.cities.map(city =>
				      <Button
				       handleClick={this.changeCity}
				       label={city}/>)}
		        </div>
		    </div>
		</div>
		<div>	            
		    <Map	                        
	                options={{
		            city: this.state.city,
		            center: this.state.source.center,
		            zoom: this.state.source.zoom
			}} 
	                source={{
		            type: "FeatureCollection",
		            features: this.state.features
			}}
	                layer={{
		            id: this.state.layer.id,
	                    label: this.state.layer.label,
		            dataSource: this.state.layer.dataSource,
		            headers: [this.state.source.joinField, this.state.layer.id],
			    values: this.state.features.map(d => [d.properties[self.state.source.joinField], d.properties[self.state.layer.id]]),
			    colors: this.colors
		        }}
	                joinField={this.state.source.joinField}
		    />
		</div>	
	     </div>
		
	)
    };
}

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

