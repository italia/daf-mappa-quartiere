import React, { Component } from 'react'
import mapboxgl from 'mapbox-gl'
import './App.css'

mapboxgl.accessToken = 'pk.eyJ1IjoiZW5qYWxvdCIsImEiOiJjaWhtdmxhNTIwb25zdHBsejk0NGdhODJhIn0.2-F2hS_oTZenAWc0BMf_uw';

class Map extends Component {
    map;

    constructor(props: Props) {
	super(props);
	this.state = {
	    hoverElement: props.hoverElement,
	    city: props.options.city,
	    property: props.layer.id,
	    clicked: "none"
	};
    }

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
	    
	    map.addSource('Quartieri', {type: 'geojson', data: props.data});
	    var layers = map.getStyle().layers;
	    // Find the index of the first symbol layer in the map style
	    this.firstSymbolId;
	    for (var i = 0; i < layers.length; i++) {
		if (layers[i].type === 'symbol') {
		    this.firstSymbolId = layers[i].id;
		    break;
		}
	    }
	    
	    map.addLayer({
		id: 'Quartieri',
		type: 'fill',
		paint: {'fill-opacity': 1},
		layout: {},
		source: 'Quartieri'
	    }, this.firstSymbolId);
	    map.setPaintProperty('Quartieri', 'fill-color', {
		property: props.layer.id,
		stops: props.layer.colors.stops
	    });
	    map.addLayer({
		id: 'Quartieri-hover',
		type: "fill",
		source: 'Quartieri',
		layout: {},
		paint: {"fill-color": props.layer.colors.highlight, "fill-opacity": 1},
		filter: ["==", props.joinField, props.hoverElement]
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
		map.setFilter('Quartieri-hover', ['==', props.joinField, e.features[0].properties[props.joinField]]);
		var features = map.queryRenderedFeatures(e.point);
		props.onHover(e.features[0]);
            });
	    map.on('mouseout', 'Quartieri', function() {
		map.setFilter('Quartieri-hover', ['==', props.joinField, props.hoverElement]);
	    });
	    map.on('click', 'Quartieri', function(e) {
		var clicked = e.features[0].properties[props.joinField];
		self.setState({ clicked: clicked });
                map.setFilter('Quartieri-click', ['==', props.joinField, clicked]);
		props.onClick(e.features[0]);
            });

	});
    }

    componentDidMount() {
	this.createMap();
    };
    
    componentDidUpdate() {
	const props = this.props;
	if (props.hoverElement !== 'none') {
	    this.map.setFilter('Quartieri-hover', ['==', props.joinField, props.hoverElement]);
	}
	if (props.options.city !== this.state.city || props.layer.id !== this.state.property) {
            this.map.remove();
            this.createMap();
	    this.setState({city: props.options.city, property: props.layer.id});
	    this.setState({ clicked: "none" });
	}
    };

    
    render() {
	var color = "white";
	var title = "Clicca su un poligono";
	if (this.state.clicked !== "none") {
	    console.log(this.props)
	    if (this.state.city === "Torino") {
		var NCIRCO = this.state.clicked;
		var joinfield = this.props.joinField;
		title = this.props.data.features.filter(d => d.properties[joinfield] === NCIRCO)[0].properties.DENOM;
	    } else {
		title = this.state.clicked;
	    }
	    color = "red";
	}
	 	
	return (
           <div style={{ display: "flex", flexDirection: "column" }}>
	        <div id="popUp" style={{ backgroundColor: color }}><p >{title}</p></div>	
                <div id="mapContainer"
	            ref={el => this.mapContainer = el}
	            style={{ height: "80vh", width: "70vw" }}>
		</div>
	     </div>
	);
    };
}
    
export default Map;
