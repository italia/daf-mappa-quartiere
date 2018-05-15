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

    /*shouldComponentUpdate(nextProps, nextState) {
	console.log("nextProps");
	console.log(nextProps)
	if (this.props.city != nextProps.options.city) {
	    this.map.remove();
	    this.setState({
		city: nextProps.options.city,
		property: nextProps.layer.id,
		neighborhood: "none"
	    });
	    this.createMap(); 
	}
	return true;
    };*/
	
    componentWillReceiveProps(nextProps) {
	if (this.props.hoverElement !== nextProps.hoverElement) {
	    this.setState({ hoverElement: nextProps.hoverElement });
	}
	if (this.props.neighborhood !== nextProps.neighborhood) {
	    this.setState({ neighborhood: nextProps.neighborhood });
	}
	if (this.props.city != nextProps.options.city) {
	    if (this.map !== undefined) {
		this.map.remove();
		this.setState({
		    city: nextProps.options.city,
		    property: nextProps.layer.id,
		    neighborhood: "none"
		});
	    }
	}
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
	    
	    map.addSource('Quartieri', {type: 'geojson', data: props.source});
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
		//self.setState({hoverElement: hoverElement});
            });
	    map.on('mouseout', 'Quartieri', function() {
		self.setState({ hoverElement: "none" }); 
		map.setFilter('Quartieri-hover', ['==', props.joinField, ""]);
		//self.setState({ hoverElement: "none" });
	    });
	    map.on('click', 'Quartieri', function(e) {
		var neighborhood = e.features[0].properties;
		var clicked = neighborhood[props.joinField];
		self.setState({ neighborhood: neighborhood });
		map.setFilter('Quartieri-click', ['==', props.joinField, clicked]);
		//self.setState({ neighborhood: neighborhood });
            });
	});
    };
    /*
    componentDidMount() {
	this.createMap();
    };*/
    
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
	console.log(this.state)
	var nameField = "NIL";
	if (this.state.city === "Torino")
	    nameField = "DENOM";
	
	var clicked = (this.state.neighborhood === "none") ?
	    "none" :
	    this.state.neighborhood[this.props.joinField];
	
	var self = this;
	return (  
	    <div>
                <div id='mapContainer'
	            ref={el => this.mapContainer = el}
	            style={{
		        height: '90vh',
			width: '100vw'
		    }}/>
		
		<div className='map-overlay'
	            id='chart'
	            style={{
		        height: '85vh',
			width: '25vw',
			top: '80px',
			right: '10px'
		    }}>
                    <BarChart
	                style={{
		            width: 700,
			    height: 950
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
	            id='legend'
	            style={{
		        height: '8vh',
			width: '28vw',
			right: '500px',
			bottom: '0px'
		    }}>
                    <Legend
                        stops={this.props.layer.colors.stops}
                        style={{
		            height: '30',
			    width: '300'
			}}
                    />                                  
                </div>
		
                <Dashboard
	            neighborhood={this.state.neighborhood}
	            nameField={nameField}

	            list={[{
		        label: "Numero di abitanti",
			value: Math.floor(15000 * Math.random()),
			dataSource: "dati simulati",
			unit: ""
		    },{
			label: "Area",
			field: "AreaHA",
		        dataSource: "Comune di Milano",
			unit: "ettari"
		    }]}

	            piechart={{
			title: "Situazione occupazionale",
			labels: ["occupati", "disoccupati", "in cerca di lavoro"],
			values: [Math.random() * 903, Math.random() * 100, Math.random() * 200],
			colors: [ "#9e0142", "#fdae61", "#abdda4"],
			dataSource: "dati simulati"
		    }}

	            barchart2withlegend={{
			title: "Popolazione per fasce d'età",
			data1: {
			    values: [10, 14, 15, 18, 21, 19, 15, 8, 4, 2, 1],
			    label: "donne",
			    color: "pink"
			},
			data2: {
			    values: [12, 15, 18, 18, 22, 24, 14, 10, 5, 3, 1],
			    label: "uomini",
			    color: "blue"
			},
			labels: ['0-9', '10-19', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90-99', '100-109'],
			dataSource: "dati simulati"
		    }}
	    
	            style={{
		        height: '55vh',
			width: '30vw',
			top: '90px',
			left: '30px'
		    }}
		/>
	    </div>	   
	);
    };
}
    
export default Map;
