import React, { Component } from 'react'
import mapboxgl from 'mapbox-gl'
import './App.css'
import BarChart from './BarChart';
import Legend from './Legend';
import Dashboard from './Dashboard';

mapboxgl.accessToken = 'pk.eyJ1IjoiZW5qYWxvdCIsImEiOiJjaWhtdmxhNTIwb25zdHBsejk0NGdhODJhIn0.2-F2hS_oTZenAWc0BMf_uw';

class Map extends Component {
    map;
    
    constructor(props: Props) {
	super(props);
	
	this.state = {
	    hoverElement: "none",
	    city: props.options.city,
	    property: props.layer.id,
	    neighborhood: "none"
	};

	this.onHoverBarChart = this.onHoverBarChart.bind(this);
	this.onMouseOutBarChart = this.onMouseOutBarChart.bind(this);
	this.onClickBarChart = this.onClickBarChart.bind(this);
    };
    
    componentWillReceiveProps(nextProps) {
	if (this.props.hoverElement !== nextProps.hoverElement) {
	    this.setState({ hoverElement: nextProps.hoverElement });
	}
	if (this.props.neighborhood !== nextProps.neighborhood) {
	    this.setState({ neighborhood: nextProps.neighborhood });
	}
	if (this.props.layer.id != nextProps.layer.id) {
	    if (this.map !== undefined) {
		this.map.remove();
		this.setState({
                    property: nextProps.layer.id,
		    neighborhood: "none"
		});
	    }
	    this.createMap();
	}
	if (this.props.options.city != nextProps.options.city) {
	    if (this.map !== undefined) {
		this.map.remove();
		this.setState({
		    city: nextProps.options.city,
		    property: nextProps.layer.id,
		    neighborhood: "none"
		});
	    }
	    this.createMap(); //todo: do not update map if city doesn't change
	}

    };

    componentDidMount() {
	this.createMap();
    };
    
    createMap() {
	this.map = new mapboxgl.Map({
            container: this.mapContainer,
            style: 'mapbox://styles/mapbox/light-v9',
            center: this.props.options.center,
            zoom: this.props.options.zoom
        });

	this.map.on('load', () => {
	    var map = this.map;
	    var props = this.props;
	    var self = this;
	    
	    map.addSource('Quartieri', {
		type: 'geojson',
		data: props.source
	    });
	    
	    var layers = map.getStyle().layers;

	    // Find the index of the first symbol layer in the map style
	    this.firstSymbolId;
	    for (var i = 0; i < layers.length; i++) {
		if (layers[i].type === 'symbol') {
		    this.firstSymbolId = layers[i].id;
		    break;
		}
	    };
	    
	    map.addLayer({
		id: 'Quartieri',
		type: 'fill',
		paint: {'fill-opacity': 1},
		layout: {},
		source: 'Quartieri'
	    }, this.firstSymbolId);
	    map.setPaintProperty('Quartieri',
				 'fill-color',
				 {
		property: props.layer.id,
		stops: props.layer.colors.stops
	    });
	    map.addLayer({
		id: 'Quartieri-hover',
		type: "fill",
		source: 'Quartieri',
		layout: {},
		paint: {"fill-color": props.layer.colors.highlight, "fill-opacity": 1},
		filter: ["==", props.joinField, this.state.hoverElement]
	    }, this.firstSymbolId);
	    map.addLayer({
		id: 'Quartieri-line',
		type: 'line',
		paint: {'line-opacity': 0.25},
		source: 'Quartieri'
	    }, this.firstSymbolId);
	    map.addLayer({
                id: 'Quartieri-click',
                type: "fill",
                source: 'Quartieri',
                layout: {},
                paint: {"fill-color": "red", "fill-opacity": 1},
                filter: ["==", props.joinField, ""]
            }, this.firstSymbolId);
/*
	    //add geojson with data points
	    if (props.layer.raw !== "none") {
		map.addSource(props.layer.id + "_raw", {
		    type: 'geojson',
		    data: props.layer.raw.data
		})

		map.addLayer({
		    id: props.layer.id + "_raw_layer", 
		    type: "circle",
		    source: props.layer.id + "_raw",
		    paint: {
			"circle-radius": 3,
			"circle-color": props.layer.raw.color
		    }
		});
	    }
*/	    
	    map.on('mousemove', 'Quartieri', function(e) {
		console.log("moving mouse")
		var hoverElement = e.features[0].properties[props.joinField];
		self.setState({ hoverElement: hoverElement }); 
		map.setFilter('Quartieri-hover', ['==', props.joinField, hoverElement]);
            });
	    map.on('mouseout', 'Quartieri', function() {
		console.log("mouseout")
		self.setState({ hoverElement: "none" }); 
		map.setFilter('Quartieri-hover', ['==', props.joinField, ""]);
	    });
	    map.on('click', 'Quartieri', function(e) {
		var neighborhood = e.features[0].properties;
		var clicked = neighborhood[props.joinField];
		self.setState({ neighborhood: neighborhood });
		map.setFilter('Quartieri-click', ['==', props.joinField, clicked]);
            });
	});
    };
    
    onHoverBarChart(d) {
	this.map.setFilter('Quartieri-hover', ['==', this.props.joinField, d[0]]);
	this.setState({ hoverElement: d[0] });
    };

    onMouseOutBarChart(d) {
	this.map.setFilter('Quartieri-hover', ['==', this.props.joinField, ""]);
	this.setState({ hoverElement: "none" });
    };

    onClickBarChart(d) {
	var props = this.props;
	
	var clicked = d[0];
	var neighborhood = props.source
	    .features
	    .filter(d => {
		return d.properties[props.joinField] === clicked;
	    })[0]
	    .properties;
	this.map.setFilter('Quartieri-click', ['==', props.joinField, clicked]);
	this.setState({ neighborhood: neighborhood });
    };
    
    render() {
	var clicked = (this.state.neighborhood === "none") ?
	    "none" :
	    this.state.neighborhood[this.props.joinField];
	
	var self = this;
	return (  
	    <div>
                <div id='mapContainer'
	            ref={el => this.mapContainer = el}/>
		
		<div className='map-overlay'
	            id='chart'>
                    <BarChart
	                style={{
		            width: 350,
			    height: 1200
			}}
                        hoverElement={this.state.hoverElement}        
                        onHover={this.onHoverBarChart}
                        onMouseOut={this.onMouseOutBarChart}
                        onClick={this.onClickBarChart}         
                        clicked={clicked}
                        data={{
                            city: this.props.options.city, 
                            label: this.props.layer.label,
                            dataSource: this.props.layer.dataSource,
                            headers: [this.props.joinField, this.props.layer.id],
                            values: this.props.source.features.map(d => [d.properties[self.props.joinField], d.properties[self.props.layer.id]]), 
                            colors: this.props.layer.colors 
                        }}             
                   />           
                </div>
	                    
		<div className='legend-overlay'
	            id='legend'>
                    <Legend
                        stops={this.props.layer.colors.stops}
                        style={{
		            width: 500,
		            height: 30
			}}
                    />                                  
                </div>
		
                <Dashboard
	            neighborhood={this.state.neighborhood}
	            nameField={this.props.nameField}
                    dashboard={this.props.dashboard}
		/>
	    </div>	   
	);
    };
}
    
export default Map;
