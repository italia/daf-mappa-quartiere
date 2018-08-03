import React, { Component } from 'react';
import './App.css';
import Map from './Map';
import Dropdown from './Dropdown';

var localhost = "http://localhost:4000/";

function getMenuUrl() {
    return localhost + "menu.json";
};

class App extends Component { 
    
    constructor(props) {
	super(props);
	this.state = {
            city: "Milano",
            cityMenu: [],
            source: "none",
            layer: "none",
            categories: [],
            cities: [],
	    features: []
        };
	
	this.changeCity = this.changeCity.bind(this);
        this.changeLayer = this.changeLayer.bind(this);
    };

    componentDidMount() {
	this.fetchMenu();
    };
    
    /*
    writeDashboardFile(jsonLayer) {
	var m = jsonLayer.map(v => {
	    
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
            v["DAF21"] = 100 * v.ST9/v.ST1;
            v["DAF22"] = 100 * v.ST10/v.ST1;
	    v["DAF23"] = 100 * v.ST11/v.ST1;
            v["DAF24"] = 100 * v.ST12/v.ST1; 
            v["DAF25"] = 100 * v.ST13/v.ST1;
            v["DAF26"] = 100 * v.ST14/v.ST1;
            return v;
        });
        console.log(JSON.stringify(m.map(v => {return {
            P1: v.P1,
            P61: v.P61,
            P62: v.P62,
            P47: v.P47,
            P48: v.P48,
            P49: v.P49,
            P50: v.P50,
            P51: v.P51,
            P52: v.P52,
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
            DAF20: v.DAF20,
	    DAF21: v.DAF21,
	    DAF22: v.DAF22,
	    DAF23: v.DAF23,
	    DAF24: v.DAF24,
	    DAF25: v.DAF25,
	    DAF26: v.DAF26	    
        }})))
	}
*/
    	
    fetchMenu() {
	var url = getMenuUrl();
	
        return fetch(url)
	    .then((response) => response.json())
            .then((fullMenu) => {

		var cities = [];
                fullMenu.forEach((l) => {
                    if (cities.indexOf(l.city) === -1) {
                        cities.push(l.city);
                    }
                });
		
		var cityMenu = fullMenu.filter((l) => l.city === this.state.city); 
		var source = {
		    index: cityMenu
			.map((l) => l.type)
			.indexOf("source")
		};
		var defaultLayer = cityMenu
		    .map((l, index) => {
		    if (l.indicators !== undefined) {
			var indicatorIndex = l.indicators.map((d) => d.default).indexOf(true);
			return {index: index, indicatorIndex: indicatorIndex};
		    } else {
			return {index: index, indicatorIndex: -1};
		    }
		})
		    .filter((l) => l.indicatorIndex > -1)[0];

		var categories = [];
		cityMenu.forEach((l) => {
		    if (l.indicators !== undefined) {
			l.indicators
			    .map((i) => i.category)
			    .forEach((c) => {
				if (categories.indexOf(c) === -1)
				    categories.push(c);
			    })
		    }
		});
		var joinField = cityMenu[source.index].joinField;
		
		Promise.all(cityMenu.map((l) =>
					 fetch(localhost + l.url)
					 .then(response => response.json())))
                    .then((jsons) => {
			var features = jsons[source.index].features;			
			var quartieri = features.map((f) => f.properties[joinField]);
			
			jsons.map((json, i) => {
		            if (i !== source.index) {
				var jsonQuartieri = json.map((j) => j[joinField]);
				var mapping = quartieri.map((q) => jsonQuartieri.indexOf(q));
				
				cityMenu[i].indicators.map((l) => l.id)
				    .map((jsonField) => 
					features.forEach((f, q) => {
					    var v = json[mapping[q]][jsonField];
					    features[q].properties[jsonField] = (Array.isArray(v)) ? averageArray(v) : v;
					})
				    );
				//  this.writeDashboardFile(jsonLayer)                        	
			    }
			});
			
			this.setState({
			    cityMenu: cityMenu,
			    source: source,
			    layer: defaultLayer,
			    categories: categories,
			    cities: cities,
			    features: features
			});		
                    });           
	    });
    };
    
    changeCity(d, label) {
        if (this.state.city !== label) {
            this.setState({
		city: label,
		layer: "none",
		source: "none",
		cityMenu: [],
		features: []
            });
        }
    };

    getLayerByLabel(label) {
	var layer = this.state.cityMenu.map((l, index) => {
	    if (l.indicators !== undefined) {
		var indicatorIndex = l.indicators.map((d) => d.label).indexOf(label);
		return { index: index, indicatorIndex: indicatorIndex };
	    } else {
		return { index: index, indicatorIndex: -1};
	    }
	})
	    .filter((l) => l.indicatorIndex > -1)[0];
	return layer;
    };

    getLayerByCategory(c) {
	var layers = this.state.cityMenu.reduce((a, l, index) => {
	    
	    if (l.indicators !== undefined) {
		
		l.indicators.forEach((i, indicatorIndex) => {
		    if (i.category === c) {
			a.push({index: index, indicatorIndex: indicatorIndex});
		    }
		});
            }
	    return a;
	}, []);
	return layers;
    };

    getLayer(layer) {
	return this.state.cityMenu[layer.index].indicators[layer.indicatorIndex];
    };

    getCategoryMenu(category) {
	return this.getLayerByCategory(category)
            .map((l) => {
                return this.state.cityMenu[l.index]
                    .indicators[l.indicatorIndex]
                    .label;
            });
    };
    
    changeLayer(d, label) {
	var currentLayer = this.getLayer(this.state.layer);
	if (currentLayer.label !== label) {
	    this.setState({layer: this.getLayerByLabel(label)});
        }
    };
	        
    render() {	
	var self = this;
	if (self.state.features.length === 0) {
	    return null;
	} else {
	    var source = this.state.cityMenu[this.state.source.index];
            var layer = this.state.cityMenu[this.state.layer.index].indicators[this.state.layer.indicatorIndex];
	    console.log(layer.dataSource)
	    if (layer.dataSource === undefined) {
		console.log(this.state.cityMenu[this.state.layer.index]);
		layer.dataSource = this.state.cityMenu[this.state.layer.index].dataSource;
		console.log(layer.dataSource)
	    }
	    var values = this.state.features.map(d => d.properties[layer.id])
		.map((v) => {if (Array.isArray(v)) return averageArray(v); else return v;});
	    var sortedFeatures = this.state.features
		.sort((a, b) => b.properties[layer.id] - a.properties[layer.id]);
	    
	    return (
                <div className="App">
		    <div className="App-header">
		        <div style={{ display: "flex", justifyContent: "space-between" }}>
		            <div>
		                {self.state.categories
		                 .map((category, i) => 
	                              <Dropdown
				          label={category}
				          key={'dropdown_' + i}
				          dropdownContent={self.getCategoryMenu(category)}
				          handleClick={self.changeLayer}/>
			        )}
		            </div>

		            <h2>Mappa dei quartieri di {this.state.city}</h2>
                
		            <Dropdown label={this.state.city} dropdownContent={this.state.cities} handleClick={this.changeCity}/>
		        </div>
		    </div>
		    <div>	            
		        <Map	                        
	                    options={{
		                city: this.state.city,
		                center: source.center,
		                zoom: source.zoom
			    }} 
	                    source={{
		                type: "FeatureCollection",
		                features: sortedFeatures
			    }}
	                    layer={{
		                id: layer.id,
	                        label: layer.label,
		                dataSource: layer.dataSource,
		                headers: [source.joinField, layer.id],
			        colors: layer.colors,
				description: layer.description
		            }}
	                    joinField={source.joinField}
	                    nameField={source.nameField}
	                    dashboard={null}
		        />
		    </div>	
	         </div>
	    )
	}
    };
};

function averageArray(a) {
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


