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
		    id='dashboard-start'>
		    Clicca su un quartiere
		</div>
	    );
	}
	
	//to do add IDquartiere in Milano_dashboard.json
	var properties = this.props.neighborhood;
	return (
	    <div className='dashboard-overlay' id='dashboard'>
	        <div>
		    <h3 style={{textAlign: 'left'}}>
		        {properties[this.props.nameField]}
	            </h3>
		</div>
	    </div>
	);
    };
}

export default Dashboard;
