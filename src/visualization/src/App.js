import React, { Component } from 'react';
import './App.css';
import CityMenu from './CityMenu';
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
            sourceIndex: -1,
            layerIndex: [-1, -1],
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

    getCities(menu) {
	var cities = [];
	menu.forEach((l) => {
            if (cities.indexOf(l.city) === -1) {
                cities.push(l.city);
            }
        });
	return cities;
    };
    
    fetchMenu() {	
        return fetch(getMenuUrl())
	    .then((response) => response.json())
            .then((fullMenu) => {

		var cities = this.getCities(fullMenu);		
		var cityMenu = new CityMenu({ menu: fullMenu, city: this.state.city }); 
		
		var sourceIndex = cityMenu.getIndex({type: "source"});
		var defaultLayerIndex = cityMenu.getIndex({type: "layer", default: true});
		
		
		var categories = cityMenu.getCategories();
		var joinField = cityMenu.get(sourceIndex).joinField;
		
		Promise.all(cityMenu.fetch({localhost: localhost}))
		    .then((jsons) => {
			var features = jsons[sourceIndex].features;			
			var quartieri = features.map((f) => f.properties[joinField]);
			
			jsons.forEach((json, j) => {
		            if (j !== sourceIndex) {
				var jsonQuartieri = json.map((d) => d[joinField]);
				
				var mapping = quartieri.map((d) => jsonQuartieri.indexOf(d));
				
				cityMenu.get(j).indicators.map((l) => l.id)
				    .map((jsonField) => 
					features.forEach((f, d) => {
					    var v = json[mapping[d]][jsonField];
					    features[d].properties[jsonField] = (Array.isArray(v)) ? averageArray(v) : v;
					})
					);
				//define dataSource if undefined
				cityMenu.get(j).indicators.forEach((d) => {
				    if (d.dataSource === undefined) {
					d.dataSource = cityMenu.cityMenu[j].dataSource;
				    }
				})
				//  this.writeDashboardFile(jsonLayer)                        	
			    }
			});
			this.setState({
			    cityMenu: cityMenu,
			    sourceIndex: sourceIndex,
			    layerIndex: defaultLayerIndex,
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
                layerIndex: [-1, -1],
                sourceIndex: -1,
                cityMenu: [],
                features: []
            });
        }
    };
    
    changeLayer(d, label) {
	var currentLayer = this.state.cityMenu.getLayer(this.state.layerIndex);
	if (currentLayer.label !== label) {
	    this.setState({layerIndex: this.state.cityMenu.getIndex({label: label})});
        }
    };
	        
    render() {	
	var self = this;
	if (self.state.features.length === 0) {
	    return null;
	} else {
	    var source = this.state.cityMenu.getSource(this.state.sourceIndex);
            var layer = this.state.cityMenu.getLayer(this.state.layerIndex);
	    return (
                <div className="App">
		    <div className="App-header">
		        <div style={{ display: "flex", justifyContent: "space-between" }}>
		            <div>
		            {self.state.cityMenu.getCategories()
		                 .map((category, i) => 
	                              <Dropdown
				          label={category}
				          key={'dropdown_' + i}
				          dropdownContent={self.state.cityMenu.getCategoryMenu(category)}
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
	                    features={this.state.features}
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


