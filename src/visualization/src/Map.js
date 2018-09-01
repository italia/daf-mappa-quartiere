import React, { Component } from 'react'
import mapboxgl from 'mapbox-gl'
import { scaleLinear } from 'd3-scale';
import './App.css'
import BarChart from './BarChart';
import Dashboard from './Dashboard';

mapboxgl.accessToken = 'pk.eyJ1IjoiZW5qYWxvdCIsImEiOiJjaWhtdmxhNTIwb25zdHBsejk0NGdhODJhIn0.2-F2hS_oTZenAWc0BMf_uw';

class Map extends Component {
    map;
    
    constructor(props: Props) {
	super(props);
	console.log(props)
	var source = this.getSource(props);
	var layer = this.getLayer(props);
	
	this.state = {
	    city: props.city,
	    source: source,
	    layer: layer,
	    neighborhood: "none",
	    hoverNeighborhood: "none",
	    infoElement: "hidden",
	    infoHtml: ""
	};

	this.onClickBarChart = this.onClickBarChart.bind(this);
	this.onHoverBarChart = this.onHoverBarChart.bind(this);
	this.onMouseOutBarChart = this.onMouseOutBarChart.bind(this);
	this.onClickInfo = this.onClickInfo.bind(this);
    };

    getSource(props) {
	return props.cityMenu.getSource(props.sourceIndex);
    };

    getLayer(props) {
	var layer = props.cityMenu.getLayer(props.layerIndex);
        layer.values = props.features
            .sort((a, b) => b.properties[layer.id] - a.properties[layer.id])
            .map((f) => [f.properties[props.joinField], f.properties[layer.id]]);
        layer.colorArray = colorArray(layer.values.map((v) => v[1]), layer.colors);
	layer.active = "mappa";
	return layer;
    }

    addSource(props) {
	this.map.addSource('Quartieri', {
            type: 'geojson',
            data: { type: "FeatureCollection", features: props.features }
        });
    };

    addLayer(props) {
	var self = this;
	var map = this.map;
	
	var layers = map.getStyle().layers;

        // Find the index of the first symbol layer in the map style
	self.firstSymbolId = null;
        for (var i = 0; i < layers.length; i++) {
            if (layers[i].type === 'symbol') {
                self.firstSymbolId = layers[i].id;
                break;
            }
        }
	
        map.addLayer({
            id: 'Quartieri',
            type: 'fill',
            paint: {'fill-opacity': 1},
            layout: {},
            source: 'Quartieri'
        }, self.firstSymbolId);
	
        map.addLayer({
            id: 'Quartieri-hover',
            type: "fill",
            source: 'Quartieri',
            layout: {},
            paint: {"fill-color": "black", "fill-opacity": 1},
            filter: ["==", props.joinField, self.getIndexFromNeighborhood(self.state.hoverNeighborhood)]
        }, self.firstSymbolId);
	
        map.addLayer({
            id: 'Quartieri-line',
            type: 'line',
            paint: {'line-opacity': 0.25},
            source: 'Quartieri'
        }, self.firstSymbolId);
	
        map.addLayer({
            id: 'Quartieri-click',
            type: "fill",
            source: 'Quartieri',
            layout: {},
            paint: {"fill-color": "red", "fill-opacity": 1},
            filter: ["==", props.joinField, ""]
        }, self.firstSymbolId);

	map.on('mousemove', 'Quartieri', function(e) {
	    var hoverNeighborhood = e.features[0].properties;
	    map.setFilter('Quartieri-hover', ['==', props.joinField, self.getIndexFromNeighborhood(hoverNeighborhood)]);
	    self.setState({ hoverNeighborhood: hoverNeighborhood });
        });
	
        map.on('mouseout', 'Quartieri', function() {
            map.setFilter('Quartieri-hover', ['==', props.joinField, ""]);
            self.setState({ hoverNeighborhood: "none" });
        });
	
        map.on('click', 'Quartieri', function(e) {
            var neighborhood = e.features[0].properties;
            map.setFilter('Quartieri-click', ['==', props.joinField, self.getIndexFromNeighborhood(neighborhood)]);
            self.setState({ neighborhood: neighborhood });
        });
    };
    
    componentWillReceiveProps(nextProps) {
	if (this.props.city !== nextProps.city || this.props.layerIndex !== nextProps.layerIndex) {
	    var source = this.getSource(nextProps);
            var layer = this.getLayer(nextProps);

	    var map = this.map;
	    
	    if (this.props.city !== nextProps.city) {
		//clean
		map.removeLayer("Quartieri");
		map.removeLayer("Quartieri-hover");
		map.removeLayer("Quartieri-line");
		map.removeLayer("Quartieri-click");
		map.removeSource("Quartieri");

		map.setCenter(source.center);
		map.setZoom(source.zoom);
		this.addSource(nextProps);
		this.addLayer(nextProps);
	    }
	   
	    map.setPaintProperty('Quartieri',
				 'fill-color',
				 {
				     property: layer.id,
				     stops: layer.colorArray.stops
				 });

	    map.setFilter('Quartieri-click', ['==', this.props.joinField, ""]);
	    
	    this.setState({
		city: nextProps.city,
		source: source,
                layer: layer,
                neighborhood: "none"
            });	
	}
    };

    componentDidMount() {
	this.createMap();
    };

    shouldComponentUpdate(nextProps, nextState) {
	console.log(this.state.layer.active)
        console.log(nextState.layer.active)
	if (this.state.layer.active !== nextState.layer.active)
            return true;
	if (this.props.city !== nextProps.city)
	    return true;

	if (this.props.layerIndex !== nextProps.layerIndex)
	    return true;

	if (this.getIndexFromNeighborhood(this.state.neighborhood) !== this.getIndexFromNeighborhood(nextState.neighborhood))
	    return true;

	if (this.getIndexFromNeighborhood(this.state.hoverNeighborhood) !== this.getIndexFromNeighborhood(nextState.hoverNeighborhood))
            return true;

	if (this.state.infoElement !== nextState.infoElement)
	    return true;
	
	return false;
    };
    
    createMap() {
	var props = this.props;
	
	var source = this.getSource(props);
        var layer = this.getLayer(props);
	
	this.map = new mapboxgl.Map({
            container: this.mapContainer,
            style: 'mapbox://styles/mapbox/light-v9',
            center: source.center,
            zoom: source.zoom
        });
	
	var map = this.map;

	map.on('load', () => {
	    //set the language (note: this is not working)
	    map.setLayoutProperty('country-label-lg', 'text-field', ['get', 'name_it']);

	    this.addSource(this.props);
	    this.addLayer(this.props);

	    map.setPaintProperty('Quartieri',
				 'fill-color',       
                                 {          
				     property: layer.id,  
				     stops: layer.colorArray.stops  
				 });
	});
    };
	
    onHoverBarChart(d) {
	var hovered = d[0];
	this.map.setFilter('Quartieri-hover', ['==', this.props.joinField, hovered]);
	this.setState({ hoverNeighborhood: this.getNeighborhoodFromIndex(hovered) });
    };

    onMouseOutBarChart(d) {
	this.map.setFilter('Quartieri-hover', ['==', this.props.joinField, ""]);
	this.setState({ hoverNeighborhood: "none" });
    };

    onClickInfo() {
	fetch(this.props.localhost + this.state.layer.descriptionUrl)
	.then((response) => response.json())
            .then((description) => {
		this.setState({
		    infoElement: (this.state.infoElement === "hidden") ? "visible" : "hidden",
		    infoHtml : this.state.layer.description + description.value
		})
	    });
    };
    
    onClickBarChart(d) {	
	var clicked = d[0];
	this.map.setFilter('Quartieri-click', ['==', this.props.joinField, clicked]);
	this.setState({ neighborhood: this.getNeighborhoodFromIndex(clicked) });
    };

    onChangeToggle(active) {
	console.log("changing to " + active);
	if (active === "punti") {
	    if (this.state.layer.points === undefined) {
		fetch(this.props.localhost + this.state.layer.raw.url)
		    .then(response => response.json())
		    .then((points) => {
			console.log(points);
			var layer = this.state.layer;
			layer.active = "punti";
			layer.points = points;
			this.setState( {layer: layer} );
		    });
	    } else {
		this.setActiveLayerTo(active);
	    }
	} else {
	    this.setActiveLayerTo(active);
	}
    };

    setActiveLayerTo(value) {
	var layer = this.state.layer;
	layer.active = value;
	this.setState( {layer: layer} );
    };
    
    getNeighborhoodFromIndex(i) {
	var joinField = this.props.joinField;
	return this.props.features
            .filter(f => {
                return f.properties[joinField] === i;
            })[0]
            .properties;
    };

    getIndexFromNeighborhood(n) {
	var joinField =	this.props.joinField;
	return (n === "none") ? "none" : n[joinField];
    };    
	
    render() {
	const renderToggle = () => {
	    if (this.state.layer.raw !== undefined) {
		return (
		    <div className='toggle-group absolute top my120 border border--2 border--white bg-white shadow-darken10 z1'>
		        {["mappa", "punti"].map(renderEachToggle)}
		    </div>
		);
	    } else {
		return null;
	    }
	};
	
	const renderEachToggle = (active, i) => {
	    console.log(this.state.layer)
	    console.log(active)
            return (
                    <label key={i} className="toggle-container">
                    <input onChange={this.onChangeToggle(active)} checked={active === this.state.layer.active} name="toggle" type="radio" />
                        <div className="toggle txt-s py3 toggle--active-white">{active}</div>
                    </label>
            );
        };
	
	return (  
	    <div>	
                <div id='mapContainer'
	            ref={el => this.mapContainer = el}/>
	        {renderToggle()}
		<div className='map-overlay'
	            id='chart'>
		
		<i className="fa fa-info-circle" aria-hidden="true" onClick={this.onClickInfo}></i>
                    <BarChart
	                style={{
		            width: 350,
			    height: 500
			}}
	                onClick={this.onClickBarChart}
	                clicked={this.getIndexFromNeighborhood(this.state.neighborhood)}
	                onHover={this.onHoverBarChart}
	                onMouseOut={this.onMouseOutBarChart}
	                hovered={this.getIndexFromNeighborhood(this.state.hoverNeighborhood)}
                        data={{
                            city: this.state.city, 
                            label: this.state.layer.label,
                            dataSource: this.state.layer.dataSource,
                            values: this.state.layer.values,
                            colors: this.state.layer.colorArray
                        }}             
                    />
                </div>
	                 
                <Dashboard
	            city={this.state.city}
	            neighborhood={this.state.neighborhood}
	            hoverNeighborhood={this.state.hoverNeighborhood}
	            features={this.props.features}
	            ids={this.props.cityMenu.getLayerIds()}
	            labels={this.props.cityMenu.getLayerLabels()}
	            joinField={this.props.joinField}
	            nameField={this.state.source.nameField}
		/>
		
		<div className="info-overlay"
	            style={{left: (this.state.infoElement === "hidden") ? "-4000px" : "10px"}}
	            onClick={this.onClickInfo}>
	            <div dangerouslySetInnerHTML={{__html: this.state.infoHtml}}/>
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
