import React, { Component } from 'react';
import './App.css';
import CityMenu from './CityMenu';
import Map from './Map';
import Dropdown from './Dropdown';

var localhost = "http://mappa-quartiere:4000/";

function getMenuUrl() {
    return localhost + "menu.json";
};

class App extends Component { 
    menu = [];
    cities = [];
    joinField = "IDquartiere";
    
    constructor(props) {
	super(props);
	
	this.state = {
            city: "Milano",
            cityMenu: [],
	    cityCategories: [],
	    features: [],
            sourceIndex: -1,
            layerIndex: [-1, -1]
        };
	
	this.changeCity = this.changeCity.bind(this);
        this.changeLayer = this.changeLayer.bind(this);
    };

    componentDidMount() {
	fetch(getMenuUrl()) //fetch full menu
            .then((response) => response.json())
	    .then((menu) => {
		//set this.menu (the full menu with all cities)
		this.menu = menu;

		//set this.cities
	        this.menu.forEach((l) => {
		    if (this.cities.indexOf(l.city) === -1) {
			this.cities.push(l.city);
		    }
		});

		//fetch city data
		this.fetchCityData(this.state.city);
	    });
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

    fetchCityData(city) {
	var cityMenu = new CityMenu({
	    menu: this.menu,
	    city: city
	});

	var sourceIndex = cityMenu.getIndex({type: "source"});
	var defaultLayerIndex = cityMenu.getIndex({
	    type: "layer",
	    default: true
	});
	var joinField = this.joinField;

	//fetch source and layer 
	Promise.all(cityMenu.fetch({localhost: localhost}))
	    .then((jsons) => {
		var features = jsons[sourceIndex].features;
		var quartieriId1 = features.map((f) => f.properties[joinField]);
		
		jsons.forEach((layerJson, layerIndex) => {
		    
		    if (layerIndex !== sourceIndex) {
			var layer = cityMenu.get(layerIndex);
			
			var quartieriId2 = layerJson.map((d) => d[joinField]);
			if (quartieriId2.length !== quartieriId1.length) {
			    console.log("Error: the number of neighborhoods in the source file and in the layer file differ!")
			}
			var mappingId = quartieriId1.map((id) => quartieriId2.indexOf(id));
			
			layer.indicators.map((l) => l.id)
			    .map((id) => 
				 features.forEach((f, i) => {
				     var value = layerJson[mappingId[i]][id];
				     features[i].properties[id] = (Array.isArray(value)) ? averageArray(value) : value;
				 })
				);
			//define dataSource if undefined
			layer.indicators.forEach((l) => {
			    if (l.dataSource === undefined) {
				l.dataSource = layer.dataSource;
			    }
			})
			//  this.writeDashboardFile(jsonLayer)
		    }
		});
		this.setState({
		    city: city,
                    cityMenu: cityMenu,
		    cityCategories: cityMenu.getCategories(),
                    features: features,
		    sourceIndex: sourceIndex,
		    layerIndex: defaultLayerIndex
                });
            });
    };

    changeCity(d, label) {
        if (this.state.city !== label) {
            this.fetchCityData(label);
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
	    return (
                <div className="App">
		    <div className="App-header">
		        <div style={{ display: "flex", justifyContent: "space-between" }}>
		            <div>
		            {self.state.cityCategories
		                 .map((category, i) => 
	                              <Dropdown
				          label={category}
				          key={'dropdown_' + i}
				          dropdownContent={self.state.cityMenu.getCategoryMenu(category)}
				          handleClick={self.changeLayer}/>
			        )}
		            </div>

		            <h2>Mappa dei quartieri di {self.state.city}</h2>
                
		            <Dropdown label={"Cambia città"} dropdownContent={self.cities} handleClick={self.changeCity}/>
		        </div>
		    </div>
		    <div>	            
		        <Map
	                    city={self.state.city}
                            cityMenu={self.state.cityMenu}
	                    joinField={self.joinField}
		            sourceIndex={self.state.sourceIndex}
                            layerIndex={self.state.layerIndex}
	                    features={self.state.features}
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


