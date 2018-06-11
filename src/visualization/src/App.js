import React, { Component } from 'react';
import { range } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import './App.css';
import Map from './Map';
import Button from './Button';
import Menu from './Menu';
import MenuObject from './MenuObject';

var localhost = "http://localhost:4000/";
var colors = ['#FFFFDD',
              '#AAF191',
              '#80D385',
              '#61B385',
              '#3E9583',
              '#217681',
              '#285285',
              '#1F2D86',
              '#000086'];

function getMenuUrl() {
    return localhost + "menu.json";
};

function getDashboardUrl(c) {
    return localhost + c + "/Dashboard" + c + ".json";
};

class App extends Component {
    colors = {};
    
    constructor(props) {
	super(props);

	this.state = {
	    menu: null,
            city: "Milano",
	    source: "none",
            layer: "none",
//	    layerRaw: "none",
//          layerGrid: "none",
	    features: null,
	    dashboard: null
        };
	
	this.changeCity = this.changeCity.bind(this);
        this.changeLayer = this.changeLayer.bind(this);
			/*if (defaultLayer.raw !== undefined) {
			    state.layerRaw = {
				data: jsons[2],
				color: defaultLayer.raw.color
			    };
			}
			if (defaultLayer.grid !== undefined) {
			    if (defaultLayer.raw !== undefined){
				state.layerGrid = { data: jsons[3] };
			    } else {
				state.layerGrid = { data: jsons[2] };
			    }
                            state.layerGrid.translate = defaultLayer.grid.translate;
                            state.layerGrid.scale = defaultLayer.grid.scale;
                            state.layerGrid.colorRange = defaultLayer.grid.colorRange;
			    console.log(state.layerGrid)
                            }			  
		        if (defaultLayer.raw !== undefined){
				    fetch(defaultLayer.raw.url)
					.then(response => response.json())
					.then(jsonLayerRawData => {	    
					    this.setState({
						menu: menu,
						layer: defaultLayer,
						source: defaultSource,
						features: features,
						layerRaw: {
						    data: jsonLayerRawData,
						    color: defaultLayer.raw.color
						}
					    });
					});*/
	   
    };

    componentDidUpdate() {
	
	if (this.state.dashboard === null){

            this.fetchDashboard();

	} else if (this.state.source === "none") {

            var defaultLayer = this.state.menu.getDefaultLayer(this.state.city);
            var defaultSource = this.state.menu.getDefaultSource(this.state.city, defaultLayer.sourceId);
            /*if (defaultLayer.raw !== undefined) {             
              urls.push(defaultLayer.raw.url);                                                                      
              }                                                                                                                  
              if (defaultLayer.grid !== undefined) {                                                                                               
              urls.push(defaultLayer.grid.url);                                                                                                             
              }*/

            this.fetchSource(defaultSource);

        } else if (this.state.layer ==="none") {

            var defaultLayer = this.state.menu.getDefaultLayer(this.state.city);

            this.fetchLayer(defaultLayer);
            //Promise.all(urls.map(url => fetch(url).then(response => response.json())))                               
            //    .then(jsons => {
	    
        }

    };

    
    componentDidMount() {
	
	if (this.state.menu === null) {
	    
            this.fetchMenu();
	    
	}
	
    };

    fetchDashboard() {
	var url = getDashboardUrl(this.state.city);
	fetch(url)
            .then(response => response.json())
            .then(dashboard => {
		fetch(dashboard.url)
		    .then(response => response.json())
		    .then(json => {
			dashboard.data = json;
			this.setState({
			    dashboard: dashboard
			})
		    });
            });
    };
    
    fetchSource(source) {
	return fetch(source.url)
	    .then(response => response.json())
	    .then(json => {
                this.setState({
                    source: source,
                    features: json.features
                });
            });
    };

    
    /*writeDashboardFile(jsonLayer) {
	var m = jsonLayer.map(v => {
	    console.log(v)
            v["DAF1"] = v.P60 - v.P61 - v.P62;
            v["DAF2"] = v.P1 - v.ST14;
            v["DAF3"] = v.P14 + v.P15 - v.P30 - v.P31;
            v["DAF4"] = v.P16 + v.P17 - v.P32 - v.P33;
            v["DAF5"] = v.P18 + v.P19 - v.P34 - v.P35;
            v["DAF6"] = v.P20 + v.P21 - v.P36 - v.P37;
            v["DAF7"] = v.P22 + v.P23 - v.P38 - v.P39;
            v["DAF8"] = v.P24 + v.P25 - v.P40 - v.P41;
            v["DAF9"] = v.P26 + v.P27 - v.P42 - v.P43;
            v["DAF10"] = v.P28 + v.P29 - v.P44 - v.P45;
            v["DAF11"] = v.P30 + v.P31;
            v["DAF12"] = v.P32 + v.P33;
            v["DAF13"] = v.P34 + v.P35;
            v["DAF14"] = v.P36 + v.P37;
            v["DAF15"] = v.P38 + v.P39;
            v["DAF16"] = v.P40 + v.P41;
            v["DAF17"] = v.P42 + v.P43;
            v["DAF18"] = v.P44 + v.P45;
            v["DAF19"] = v.P138/(v.P138+v.P139);
            v["DAF20"] = v.P139/(v.P138+v.P139);
            return v;
        });
        console.log(JSON.stringify(m.map(v => {return {
            P1: v.P1,
            P61: v.P61,
            P62: v.P62,
            DAF1: v.DAF1,
            DAF2: v.DAF2,
            DAF3: v.DAF3,
            DAF4: v.DAF4,
            DAF5: v.DAF5,
            DAF6: v.DAF6,
            DAF7: v.DAF7,
            DAF8: v.DAF8,
            DAF9: v.DAF9,
            DAF10: v.DAF10,
            DAF11: v.DAF11,
            DAF12: v.DAF12,
            DAF13: v.DAF13,
            DAF14: v.DAF14,
            DAF15: v.DAF15,
            DAF16: v.DAF16,
            DAF17: v.DAF17,
            DAF18: v.DAF18,
            DAF19: v.DAF19,
            DAF20: v.DAF20
        }})))
	}*/

    fetchLayer(layer) {
	return fetch(layer.layerUrl)
	    .then(response => response.json())
	    .then(jsonLayer => {
		//this.writeDashboardFile(jsonLayer)
		
		var joinField = this.state.source.joinField;
                var layerField = layer.id;
		var features = this.mergeFeatures(this.state.features, jsonLayer, joinField, layerField);
		var values = features.map((d) => d.properties[layer.id]);
                this.setColors(values);
/*
		if (layer.raw !== undefined){
		    fetch(layer.raw.url)
			.then(response => response.json())
			.then(jsonLayerRawData => {
			    this.setState({
				layer: layer,
				features: features,
				layerRaw: {
				    data: jsonLayerRawData,
				    color: layer.raw.color
				}
			    });
			});
			} else {*/
                this.setState({
                    layer: layer,
                    features: features
                });
		//layerRaw: "none"  
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
	    var value = jsonLayer[index][layerField];
	    if (Array.isArray(value)) value = sumArray(value);
   
            d.properties[layerField] = value;
        });
        features = features
            .sort((a, b) => b.properties[layerField] - a.properties[layerField]);
	return features;
    };
    	
    fetchMenu() {
	var url = getMenuUrl(); 
        return fetch(url)
	    .then(response => response.json())
            .then(json => {
		this.setState({
		    menu: new MenuObject({ data: json })
		});
	    });
    };
    
    changeCity(d, label) {
        if (this.state.city !== label) {
            this.setState({
		city: label,
		dashboard: null,
		layer: "none",
		source: "none",
		features: null
            });
        }
    };

    changeLayer(d) {
        if (this.state.layer.id !== d.id) {
            this.setState({ layer: d });
        }
    };
	
    componentWillUpdate(nextProps, nextState) {
	if (nextState.menu !== this.state.menu) {

	    if (this.state.dashboard === null){
		this.fetchDashboard();
	    }
	    
	}

	if (nextState.layer !== this.state.layer) {
	    
	    this.fetchLayer(nextState.layer);
	    
	} 	
    };
        
    render() {	
	var self = this;

	if (this.state.layer === "none") {
	    return null;
	} else {
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
	                    nameField={this.state.source.nameField}
	                    dashboard={this.state.dashboard}
		        />
		    </div>	
	         </div>
	    )
	}
    };
}

function sample(values, C) {
    var min = Math.min(...values),
        max = Math.max(...values);
    return [...Array(C).keys()]
        .map((d) => d * (max - min) / C  + min);
};


//note length of a and b should be the same                                                                                                                                
function sumArray(a) {
    var sum = 0;
    var l = 0;
    for (var i=0; i<a.length; i++) {
        if (a[i] !== "NaN"){
            l = l + 1;
	    sum = sum + a[i];
        }
    }
    return sum / l;
};

export default App;

