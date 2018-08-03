import React, { Component } from 'react'
import mapboxgl from 'mapbox-gl'
import { scaleLinear } from 'd3-scale';
import { range } from 'd3-array';
import './App.css'
import BarChart from './BarChart';
import Legend from './Legend';
import Dashboard from './Dashboard';

mapboxgl.accessToken = 'pk.eyJ1IjoiZW5qYWxvdCIsImEiOiJjaWhtdmxhNTIwb25zdHBsejk0NGdhODJhIn0.2-F2hS_oTZenAWc0BMf_uw';

class Map extends Component {
    map;
    
    constructor(props: Props) {
	super(props);

	var values = props.source.features
            .sort((a, b) => b.properties[props.layer.id] - a.properties[props.layer.id])
	    .map((f) => [f.properties[props.joinField], f.properties[props.layer.id]]);
	var colors =  colorArray(values.map((v) => v[1]), props.layer.colors);
	
	this.state = {
	    hoverElement: "none",
	    city: props.options.city,
	    layer: { id: props.layer.id, values: values, colors: colors, dataSource: props.layer.dataSource},
	    neighborhood: "none",
	    infoElement: "hidden"
	};
	
	this.onHoverBarChart = this.onHoverBarChart.bind(this);
	this.onMouseOutBarChart = this.onMouseOutBarChart.bind(this);
	this.onClickBarChart = this.onClickBarChart.bind(this);
	this.onClickInfo = this.onClickInfo.bind(this);
    };
    
    componentWillReceiveProps(nextProps) {
	if (this.props.hoverElement !== nextProps.hoverElement) {
	    this.setState({ hoverElement: nextProps.hoverElement });
	}
	if (this.props.neighborhood !== nextProps.neighborhood) {
	    this.setState({ neighborhood: nextProps.neighborhood });
	}
	if (this.props.layer.id !== nextProps.layer.id || this.props.options.city !== nextProps.options.city) {
	    if (this.map !== undefined) {
	        this.map.remove();
		var values = nextProps.source.features
		    .sort((a, b) => b.properties[nextProps.layer.id] - a.properties[nextProps.layer.id])
		    .map((f) => [f.properties[nextProps.joinField], f.properties[nextProps.layer.id]]);
		var colors = colorArray(values.map((v) => v[1]), nextProps.layer.colors);
		
		this.setState({
                    layer: {id: nextProps.layer.id, values: values, colors: colors}, 
		    neighborhood: "none"
		});
	    }
	    this.createMap();
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

	    map.setLayoutProperty('country-label-lg', 'text-field', '{name_it}');
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
		property: this.state.layer.id,
		stops: this.state.layer.colors.stops
	    });
	    map.addLayer({
		id: 'Quartieri-hover',
		type: "fill",
		source: 'Quartieri',
		layout: {},
		paint: {"fill-color": "black", "fill-opacity": 1},
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

	    map.on('mousemove', 'Quartieri', function(e) {
		var hoverElement = e.features[0].properties[props.joinField];
		self.setState({ hoverElement: hoverElement }); 
		map.setFilter('Quartieri-hover', ['==', props.joinField, hoverElement]);
            });
	    map.on('mouseout', 'Quartieri', function() {
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

    onClickInfo() {
	var x = (this.state.infoElement === "hidden") ? "10px" : "-4000px";
	this.setState({infoElement: "visible"});
    }
    
    onClickBarChart(d) {
	var props = this.props;
	
	var clicked = d[0];
	var neighborhood = props.source
	    .features
	    .sort((a, b) => b.properties[props.layer.id] - a.properties[props.layer.id])
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
		<i className="fa fa-info-circle" aria-hidden="true" onClick={this.onClickInfo}></i>

                    <BarChart
	                style={{
		            width: 350,
			    height: 850
			}}
                        hoverElement={this.state.hoverElement}        
                        onHover={this.onHoverBarChart}
                        onMouseOut={this.onMouseOutBarChart}
                        onClick={this.onClickBarChart}         
                        clicked={clicked}
                        data={{
                            city: this.props.options.city, 
                            label: this.state.layer.label,
                            dataSource: this.state.layer.dataSource,
                            values: this.state.layer.values,
                            colors: this.state.layer.colors
                        }}             
                    />
                </div>
	                    
		<div className='legend-overlay'
	            id='legend'>
                    <Legend
                        stops={this.state.layer.colors.stops}
                        style={{
		            width: 700,
		            height: 60
			}}
                    />                                  
                </div>
		
                <Dashboard
	            neighborhood={this.state.neighborhood}
	            nameField={this.props.nameField}
                    dashboard={this.props.dashboard}
		/>
		<div className="info-overlay" style={{left: (this.state.infoElement === "hidden") ? "-4000px" : "10px"}} onClick={this.onClickInfo}>
	            <div dangerouslySetInnerHTML={{__html: this.props.layer.description}}></div>
                </div>
	    </div>	   
	);
    };
};
    
function sample(values, C) {
    var min = Math.min(...values),
        max = Math.max(...values);

    return [...Array(C).keys()]
        .map((d) => d * (max - min) / (C - 1)  + min);
};

function colorArray(values, colors) {
        values = sample(values, colors.length);
        return {
            stops: values.map((d, i) => [values[i], colors[i]]),
            scale: scaleLinear().domain(values).range(colors)
        };
};

export default Map;
