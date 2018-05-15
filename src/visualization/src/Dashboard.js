import React, { Component } from 'react';
import './App.css';
import PieChartWithLegend from './PieChartWithLegend.js';
import BarChart2WithLegend from './BarChart2WithLegend.js';

function sigFigs(n, sig) {
    if (n < 1) {
	var mult = Math.pow(10, sig - Math.floor(Math.log(n) / Math.LN10) - 1);  
	return Math.round(n * mult) / mult;
    } else
	return Math.round(n);
};

/*
props.list = [{label: "Numero di abitanti", propertyField: "random"}, {label: "Area", propertyField: "AreaHA"}]
*/

class Dashboard extends Component {
    constructor(props: Props) {
	super(props);
	
	this.state = {
	    neighborhood: props.neighborhood
	};
    };

    //otherwise it's updated at each mouse move
    shouldComponentUpdate(nextProps) {
	if (nextProps.neighborhood !== this.props.neighborhood)
	    return true;
	return false;
    };
	
    render() {	
	if (this.props.neighborhood === "none") {
	    return (
		    <div
		        className='dashboard-overlay'
		        id='dashboard-start'
		        style={{
			    width: '250px',
			    height: '50px',
			    top: '300px',
			    left: '70px'}}>
		        <div
		            style={{
		                textAlign: 'middle'
			    }}>
		            Clicca su un quartiere
		        </div>
		    </div>
	    );
	}

	var self = this;
	var properties = this.props.neighborhood;
	return (
	    <div className='dashboard-overlay' id='dashboard' style={this.props.style}>
	        <div>
		    <h3 style={{textAlign: "left"}}>
		        {properties[this.props.nameField]}
		    </h3>
		    <ul style={{textAlign: "left", padding: 0}}>
		    {
		        this.props.list.map(l => {
			    var value = (l.value === undefined)? self.props.neighborhood[l.field] : l.value;
			    return <li> {l.label} : {value} {l.unit}</li>
		        })
		    }
		    </ul>
		</div>
		
		<svg width="300" height="350" style={{display: "block"}}>
		    <PieChartWithLegend
                        title={this.props.piechart.title}
                        labels={this.props.piechart.labels}
                        values={this.props.piechart.values}
                        colors={this.props.piechart.colors}
	                dataSource={this.props.piechart.dataSource}
                    />
	    	    <BarChart2WithLegend
	                title={this.props.barchart2withlegend.title}
	                data1={this.props.barchart2withlegend.data1}
	                data2={this.props.barchart2withlegend.data2}
	                labels={this.props.barchart2withlegend.labels}
	                dataSource={this.props.barchart2withlegend.dataSource}
	            />
		</svg>
	    </div>
	);
    };
}

export default Dashboard;
